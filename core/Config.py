import re
import gc
import time
import logging
import network
import requests
from random import randrange
from machine import Pin, Timer, RTC
import SoftwareTimer
from Group import Group
from api_keys import ipgeo_key
from util import (
    is_device,
    is_sensor,
    is_device_or_sensor,
    reboot,
    print_with_timestamp,
    read_wifi_credentials_from_disk
)

# Set name for module's log lines
log = logging.getLogger("Config")

# Timer re-runs startup every day at 3:00 am (reload schedule rules, sunrise/sunset times, etc)
config_timer = Timer(1)
# Used to reboot if startup hangs for longer than 1 minute
reboot_timer = Timer(2)

# Turn onboard LED on, indicates setup in progress
led = Pin(2, Pin.OUT, value=1)

# Used to dynamically import correct class for each device/sensor type
hardware_classes = {
    "devices": {
        "dimmer": "Tplink",
        "bulb": "Tplink",
        "tasmota-relay": "TasmotaRelay",
        "dumb-relay": "DumbRelay",
        "desktop": "DesktopTarget",
        "http-get": "HttpGet",
        "pwm": "LedStrip",
        "mosfet": "Mosfet",
        "api-target": "ApiTarget",
        "wled": "Wled"
    },
    "sensors": {
        "pir": "MotionSensor",
        "desktop": "DesktopTrigger",
        "dummy": "Dummy",
        "load-cell": "LoadCell",
        "si7021": "Si7021",
        "dht22": "Dht22",
        "switch": "Switch"
    }
}


# Takes name (device1 etc) and config entry, returns class instance
def instantiate_hardware(name, **kwargs):
    if is_device(name) and kwargs['_type'] not in hardware_classes['devices']:
        raise ValueError(f'Unsupported device type "{kwargs["_type"]}"')
    elif is_sensor(name) and kwargs['_type'] not in hardware_classes['sensors']:
        raise ValueError(f'Unsupported sensor type "{kwargs["_type"]}"')
    elif not is_device_or_sensor(name):
        raise ValueError(f'Invalid name "{name}", must start with "device" or "sensor"')

    # Remove schedule rules (unexpected arg)
    del kwargs['schedule']

    # Import correct module, instantiate class
    if is_device(name):
        module = __import__(hardware_classes['devices'][kwargs['_type']])
    else:
        module = __import__(hardware_classes['sensors'][kwargs['_type']])
    cls = getattr(module, module.__name__)
    return cls(name, **kwargs)


# Optional argument blocks expensive method calls that connect to wifi,
# hit APIs, instantiate classes, and build schedule rule queue.
# Primarily used in unit testing to run a subset of methods.
class Config():
    def __init__(self, conf, delay_setup=False):
        print_with_timestamp("Instantiating config object...")
        log.info("Instantiating config object...")
        log.debug(f"Config file: {conf}")

        # Load metadata parameters (included in status object used by frontend)
        self.identifier = conf["metadata"]["id"]
        self.location = conf["metadata"]["location"]
        self.floor = conf["metadata"]["floor"]

        # Nested dict of schedule rules, 1 entry for each device and sensor
        # Keys are IDs (device1, sensor2, etc), values are dict of timestamp-rule pairs
        self.schedule = {}

        # Dictionairy of keyword-timestamp pairs, used for schedule rules
        self.schedule_keywords = {'sunrise': '00:00', 'sunset': '00:00'}
        self.schedule_keywords.update(conf["metadata"]["schedule_keywords"])

        # Stores timestamp of next schedule rule reload (between 3 and 4 am)
        self.reload_time = ""

        # Load GPS coordinates (used for timezone + sunrise/sunset times, not shown in frontend)
        try:
            self.gps = conf["metadata"]["gps"]
        except KeyError:
            self.gps = ""

        # Parse all device and sensor sections into dict attributes, removed
        # after device and sensor lists populated by instantiate_peripherals
        self.device_configs = {device: config for device, config in conf.items() if is_device(device)}
        self.sensor_configs = {sensor: config for sensor, config in conf.items() if is_sensor(sensor)}
        if "ir_blaster" in conf:
            self.ir_blaster_config = conf["ir_blaster"]

        if not delay_setup:
            self.setup()

    def setup(self):
        # Connect to wifi, hit APIs for current time, sunrise/sunset timestamps
        self.api_calls()

        # Instantiate each config in self.device_configs and self.sensor_configs as
        # appropriate class, add to self.devices and self.sensors respectively
        self.instantiate_peripherals()

        # Create timers for all schedule rules expiring in next 24 hours
        self.build_queue()

        # Start timer to re-build schedule rule queue for next 24 hours around 3 am
        self.start_reload_schedule_rules_timer()

        log.info("Finished instantiating config")

    def start_reload_schedule_rules_timer(self):
        # Get current epoch time + time tuple
        epoch = time.mktime(time.localtime())
        now = time.localtime(epoch)

        # Get epoch time of 3:00 am tomorrow
        # Only needed to increment day, other parameters roll over correctly in testing
        # Timezone set to none (final arg), required for compatibility with cpython test environment
        next_reload = time.mktime((now[0], now[1], now[2] + 1, 3, 0, 0, now[6], now[7], -1))

        # Calculate miliseconds until reload, add random 0-60 minute delay to stagger API calls
        adjust = randrange(3600)
        ms_until_reload = (next_reload - epoch + adjust) * 1000

        # Get HH:MM timestamp of next reload, write to log
        self.reload_time = f"{time.localtime(next_reload + adjust)[3]}:{time.localtime(next_reload + adjust)[4]}"
        log.debug(f"Reload_schedule_rules callback scheduled for {self.reload_time} am")
        print_with_timestamp(f"Reload_schedule_rules callback scheduled for {self.reload_time} am")

        # Add timer to queue
        SoftwareTimer.timer.create(ms_until_reload, self.reload_schedule_rules, "reload_schedule_rules")

    # Populates self.devices and self.sensors by instantiating configs from self.device_configs
    # and self.sensor_configs, can only be called once
    def instantiate_peripherals(self):
        # Prevent calling again after setup complete
        if "devices" in self.__dict__ or "sensors" in self.__dict__:
            raise RuntimeError("Peripherals already instantiated")

        # Create lists for device, sensor instances
        self.devices = []
        self.sensors = []

        # Pass all device configs to instantiate_devices, populates self.devices
        self.instantiate_devices(self.device_configs)

        # Pass all sensors configs to instantiate_sensors, populates self.sensors
        self.instantiate_sensors(self.sensor_configs)

        # Instantiate IR Blaster if configured (can only have 1, driver limitation)
        # IR Blaster is not a Device subclass, has no schedule rules, and is only triggered by API calls
        if "ir_blaster_config" in self.__dict__:
            from IrBlaster import IrBlaster
            self.ir_blaster = IrBlaster(
                int(self.ir_blaster_config["pin"]),
                self.ir_blaster_config["target"],
                self.ir_blaster_config["macros"]
            )
            del self.ir_blaster_config

        # Delete device and sensor config dicts
        del self.device_configs
        del self.sensor_configs
        gc.collect()

        # Map relationships between sensors ("triggers") and devices ("targets")
        self.build_groups()

    # Takes config dict (devices only), instantiates each with appropriate class, adds to self.devices
    def instantiate_devices(self, conf):
        for device in sorted(conf):
            # Add device's schedule rules to dict
            self.schedule[device] = conf[device]["schedule"]

            try:
                # Instantiate device with appropriate class
                instance = instantiate_hardware(device, **conf[device])

                # Add instance to config.devices
                self.devices.append(instance)
            except AttributeError:
                log.critical(f"Failed to instantiate {device} ({conf[device]['_type']}), params: {conf[device]}")
                print_with_timestamp(f"ERROR: Failed to instantiate {device} ({conf[device]['_type']}")
                pass
            except ValueError:
                log.critical(f"Failed to instantiate {device}, unsupported device type {conf[device]['_type']}")
                print_with_timestamp(f"ERROR: Failed to instantiate {device}, unsupported device type {conf[device]['_type']}")

        log.debug("Finished creating device instances")

    # Takes config dict (sensors only), instantiates each with appropriate class, adds to self.sensors
    def instantiate_sensors(self, conf):
        for sensor in sorted(conf):
            # Add sensor's schedule rules to dict
            self.schedule[sensor] = conf[sensor]["schedule"]

            try:
                # Find device instances for each ID in targets list
                targets = [t for t in (self.find(target) for target in conf[sensor]["targets"]) if t]

                # Replace targets list with list of instances
                conf[sensor]['targets'] = targets

                # Instantiate sensor with appropriate class
                instance = instantiate_hardware(sensor, **conf[sensor])

                # Add the sensor instance to each of it's target's "triggered_by" list
                for t in targets:
                    t.triggered_by.append(instance)

                # Add instance to config.sensors
                self.sensors.append(instance)
            except AttributeError:
                log.critical(f"Failed to instantiate {sensor} ({conf[sensor]['_type']}, params: {conf[sensor]}")
                print_with_timestamp(f"ERROR: Failed to instantiate {sensor} ({conf[sensor]['_type']}")
                pass
            except ValueError:
                log.critical(f"Failed to instantiate {sensor}, unsupported sensor type {conf[sensor]['_type']}")
                print_with_timestamp(f"ERROR: Failed to instantiate {sensor}, unsupported sensor type {conf[sensor]['_type']}")

        log.debug("Finished creating sensor instances")

    # Maps relationships between sensors ("triggers") and devices ("targets")
    # Multiple sensors with identical targets are merged into groups (or 1 sensor per group if unique targets)
    # Main loop iterates Groups, calls Group methods to check sensor conditions and apply device actions
    def build_groups(self):
        # Stores completed Group instances
        self.groups = []

        sensor_list = self.sensors.copy()

        while len(sensor_list) > 0:
            # Get first sensor in sensor_list, add to group list
            s = sensor_list.pop(0)
            group = [s]

            # Find all sensors with identical targets, add to group list
            for i in sensor_list:
                if i.targets == s.targets:
                    group.append(i)

            # Delete all sensors in group from sensor_list
            for i in group:
                try:
                    del sensor_list[sensor_list.index(i)]
                except ValueError:
                    pass

            # Instantiate group object from list of sensors
            instance = Group("group" + str(len(self.groups) + 1), group)
            self.groups.append(instance)

            # Pass instance to all members' group attributes, allows group members to access group methods
            for sensor in instance.triggers:
                sensor.group = instance
                # Add Sensor's post-action routines (if any), will run after group turns targets on/off
                sensor.add_routines()

            for device in instance.targets:
                device.group = instance

    # Called by status API endpoint, frontend polls every 5 seconds while viewing node
    # Returns object with metadata + current status info for all devices and sensors
    def get_status(self):
        # Populate template from class attributes
        status_dict = {
            "metadata": {
                "id": self.identifier,
                "floor": self.floor,
                "location": self.location,
                "schedule_keywords": self.schedule_keywords,
                "next_reload": self.reload_time,
                "ir_blaster": bool("ir_blaster" in self.__dict__)
            },
            "devices": {},
            "sensors": {}
        }

        # Add IR targets if IR Blaster configured
        if "ir_blaster" in self.__dict__:
            status_dict["metadata"]["ir_targets"] = self.ir_blaster.target

        # Iterate devices, add get_status return value, add schedule rules
        for i in self.devices:
            status_dict["devices"][i.name] = i.get_status()
            status_dict["devices"][i.name]["schedule"] = self.schedule[i.name]

        # Iterate sensors, add get_status return value, add schedule rules
        for i in self.sensors:
            status_dict["sensors"][i.name] = i.get_status()
            status_dict["sensors"][i.name]["schedule"] = self.schedule[i.name]

        return status_dict

    # Connect to wifi (if not connected), set system time from API, get sunrise/sunset times from API
    def api_calls(self):
        # Auto-reboot if startup doesn't complete in 1 min (prevents API calls hanging, canceled at bottom of function)
        reboot_timer.init(period=60000, mode=Timer.ONE_SHOT, callback=reboot)

        # Turn onboard LED on, indicates setup in progress
        led = Pin(2, Pin.OUT, value=1)

        # Connect to wifi
        wlan = network.WLAN(network.WLAN.IF_STA)
        wlan.active(True)
        if not wlan.isconnected():
            credentials = read_wifi_credentials_from_disk()
            log.debug(f"Attempting to connect to {credentials['ssid']}")
            wlan.connect(credentials["ssid"], credentials["password"])

            # Wait until finished connecting before proceeding
            while not wlan.isconnected():
                continue
            else:
                print_with_timestamp(f"Successfully connected to {credentials['ssid']}")
                log.info(f"Successfully connected to {credentials['ssid']}")

        failed_attempts = 0

        # Ensure enough free ram for API resopnse
        gc.collect()

        # Set time from internet in correct timezone, retry until successful (ntptime easier but no timezone support)
        while True:
            try:
                # Use GPS coordinates if present, otherwise rely on IP lookup
                url = f"https://api.ipgeolocation.io/astronomy?apiKey={ipgeo_key}"
                if self.gps:
                    url += f"&lat={self.gps['lat']}&long={self.gps['lon']}"

                response = requests.get(url)

                # Parse time parameters
                hour, minute, second = response.json()["current_time"].split(":")
                second, milisecond = second.split(".")

                # Parse date parameters
                year, month, day = map(int, response.json()["date"].split("-"))

                # Set RTC (uses different parameter order than time.localtime)
                RTC().datetime((year, month, day, 0, int(hour), int(minute), int(second), int(milisecond)))

                # Set sunrise/sunset times
                self.schedule_keywords["sunrise"] = response.json()["sunrise"]
                self.schedule_keywords["sunset"] = response.json()["sunset"]
                response.close()
                break

            # Issue with response object
            except KeyError:
                print_with_timestamp(f'ERROR (ipgeolocation.io): {response.json()["message"]}')
                log.error(f'ERROR (ipgeolocation.io): {response.json()["message"]}')
                reboot()

            # Network issue
            except OSError:
                print_with_timestamp("Failed to set system time, retrying...")
                log.debug("Failed to set system time, retrying...")
                failed_attempts += 1
                if failed_attempts > 5:
                    log.info("Failed to set system time 5 times, reboot triggered")
                    reboot()
                time.sleep_ms(1500)  # If failed, wait 1.5 seconds before retrying
                gc.collect()  # Free up memory before retrying
                pass

        log.info("Finished API calls (timestamp may look weird due to system clock change)")

        # Stop timer once API calls finish
        reboot_timer.deinit()

        # Turn off LED to confirm setup completed successfully
        led.value(0)

    # Receives a dictionairy of schedule rules with HH:MM timestamps
    # Returns a dictionairy of the same rules with unix epoch timestamps (next run only)
    # Called every day at 3:00 am since epoch times only work once
    def convert_rules(self, rules):
        # Create empty dict to store new schedule rules
        result = {}

        # Replace keywords with timestamp from dict, timestamps convert to epoch below
        for keyword in self.schedule_keywords:
            if keyword in rules:
                keyword_time = self.schedule_keywords[keyword]
                rules[keyword_time] = rules[keyword]
                del rules[keyword]

        # Get rule start times, sort chronologically
        schedule = list(rules)
        schedule.sort()

        # Get epoch time in current timezone
        epoch = time.mktime(time.localtime())
        # Get time tuple in current timezone
        now = time.localtime(epoch)

        for rule in schedule:
            # Skip unconverted keywords
            if not re.match("^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$", rule):
                continue

            # Get epoch time of rule using current date params, substitute hour + min from rule, substitute 0 for second
            # Timezone set to none (final arg), required for compatibility with cpython test environment
            params = (now[0], now[1], now[2], int(rule.split(":")[0]), int(rule.split(":")[1]), 0, now[6], now[7], -1)
            trigger_time = time.mktime(params)

            # Add to results: Key = unix timestamp, value = value from original rules dict
            result[trigger_time] = rules[rule]
            # Add same rule with timestamp 24 hours earlier (ensure expired rules exist, used to find current_rule)
            result[trigger_time - 86400] = rules[rule]
            # Add same rule with timestamp 24 hours later (moves rules that have already expired today to tomorrow)
            result[trigger_time + 86400] = rules[rule]

        # Get chronological list of rule timestamps
        schedule = []
        for rule in result:
            schedule.append(rule)
        schedule.sort()

        # Find the currently active rule (last rule with timestamp before current time)
        for rule in schedule:
            if epoch > rule:
                current = rule
            else:
                break

        # Delete all expired rules except current
        for rule in schedule:
            if not rule == current:
                del result[rule]
            else:
                break

        # Return the finished dictionairy
        return result

    # Add callbacks for all schedule rules to SoftwareTimer queue
    def build_queue(self):
        # Delete all existing schedule rule timers to avoid conflicts
        SoftwareTimer.timer.cancel("scheduler")

        for i in self.schedule:
            # Convert copy (preserve sunrise/sunset keywords in original)
            rules = self.convert_rules(self.schedule[i].copy())

            # Get target instance
            instance = self.find(i)
            # Skip if unable to find instance
            if not instance: continue

            # If no schedule rules, use default_rule and skip to next instance
            if len(rules) == 0:
                # If default is valid, also set as scheduled_rule
                if instance.set_rule(instance.default_rule):
                    instance.scheduled_rule = instance.current_rule
                # If default rule is invalid, disable instance to prevent unpredictable behavior
                else:
                    log.critical(f"{instance.name} invalid default rule ({instance.default_rule}), disabling instance")
                    instance.current_rule = "disabled"
                    instance.scheduled_rule = "disabled"
                    instance.default_rule = "disabled"
                    instance.disable()
                continue

            # Get list of timestamps, sort chronologically
            queue = []
            for j in rules:
                queue.append(j)
            queue.sort()

            # Set target's current_rule (set_rule method passes to validator, returns True if valid, False if not)
            if instance.set_rule(rules[queue.pop(0)]):
                # If rule valid, set as scheduled_rule
                instance.scheduled_rule = instance.current_rule
            else:
                # If rule is invalid, fall back to default rule
                log.error(f"{instance.name} scheduled rule failed validation, falling back to default rule")
                if instance.set_rule(instance.default_rule):
                    instance.scheduled_rule = instance.current_rule
                else:
                    # If both scheduled and default rules invalid, disable instance to prevent unpredictable behavior
                    log.critical(f"{instance.name} invalid default rule ({instance.default_rule}), disabling instance")
                    instance.current_rule = "disabled"
                    instance.scheduled_rule = "disabled"
                    instance.default_rule = "disabled"

            # TODO rely on set_rule method to disable?
            if str(instance.current_rule).lower() == "disabled":
                instance.disable()

            # Clear target's queue
            instance.rule_queue = []

            # Populate target's queue with chronological rule values
            for k in queue:
                instance.rule_queue.append(rules[k])

            # Get epoch time in current timezone
            epoch = time.mktime(time.localtime())

            # Create timers for all rules
            for k in queue:
                miliseconds = (k - epoch) * 1000
                SoftwareTimer.timer.create(miliseconds, instance.next_rule, "scheduler")
                gc.collect()

        print_with_timestamp(f"Finished building queue, total timers = {len(SoftwareTimer.timer.queue)}")
        log.debug(f"Finished building queue, total timers = {len(SoftwareTimer.timer.queue)}")

    # Takes ID (device1, sensor2, etc), returns instance or False
    def find(self, target):
        if is_device(target):
            for i in self.devices:
                if i.name == target:
                    return i
            else:
                log.debug(f"Config.find: Unable to find {target}")
                return False

        elif is_sensor(target):
            for i in self.sensors:
                if i.name == target:
                    return i
            else:
                log.debug(f"Config.find: Unable to find {target}")
                return False

        else:
            log.debug(f"Config.find: Unable to find {target}")
            return False

    # Called by timer every day at 3 am, regenerate timestamps for next day (epoch time)
    def reload_schedule_rules(self):
        print_with_timestamp("Reloading schedule rules...")
        log.info("Callback: Reloading schedule rules")
        # Get up-to-date sunrise/sunset, set system clock (in case of daylight savings)
        self.api_calls()

        # Create timers for all schedule rules expiring in next 24 hours
        self.build_queue()

        # Set timer to run again tomorrow between 3-4 am
        self.start_reload_schedule_rules_timer()
