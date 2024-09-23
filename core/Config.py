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
from hardware_classes import hardware_classes

# Set name for module's log lines
log = logging.getLogger("Config")

# Timer re-runs startup every day at 3:00 am
# (reload schedule rules, sunrise/sunset times, etc)
config_timer = Timer(1)
# Used to reboot if startup hangs for longer than 1 minute
reboot_timer = Timer(2)

# Turn onboard LED on, indicates setup in progress
led = Pin(2, Pin.OUT, value=1)


def instantiate_hardware(name, **kwargs):
    '''Takes name (device1, sensor2, etc) and dict of config params,
    instantiates correct driver class and returns instance.
    '''
    if is_device(name) and kwargs['_type'] not in hardware_classes['devices']:
        raise ValueError(f'Unsupported device type "{kwargs["_type"]}"')
    elif is_sensor(name) and kwargs['_type'] not in hardware_classes['sensors']:
        raise ValueError(f'Unsupported sensor type "{kwargs["_type"]}"')
    elif not is_device_or_sensor(name):
        raise ValueError(
            f'Invalid name "{name}", must start with "device" or "sensor"'
        )

    # Remove schedule rules (unexpected arg)
    del kwargs['schedule']

    # Import correct module, instantiate class
    if is_device(name):
        module = __import__(hardware_classes['devices'][kwargs['_type']])
    else:
        module = __import__(hardware_classes['sensors'][kwargs['_type']])
    cls = getattr(module, module.__name__)
    return cls(name, **kwargs)


class Config():
    '''Takes dict parsed from config.json, sets up node, peripherals, and
    scheduled rule changes based on config file settings.

    Makes API calls to set system clock and get local sunrise/sunset times used
    in schedule rules (uses GPS coordinates in config file if present).

    Instantiates correct driver for all devices and sensors specified in config
    file, creates callback timers for each scheduled rule change.

    Public attributes:
      devices:           List of device driver instances
      sensors:           List of device sensor instances
      schedule_keywords: Dict with keywords as keys, HH:MM timestamps as values

    Public methods:
      find:              Takes device or sensor ID, returns matching instance
      get_status:        Generates status dict returned by status API endpoint
      reload_schedule_rules: Updates sunrise/sunset times from API and creates
                         scheduled rule change callback timers for next day

    Optional delay_setup argument used in unit tests to prevent automatically
    running all methods (allows checking state in between each method).
    '''

    def __init__(self, conf, delay_setup=False):
        print_with_timestamp("Instantiating config object...")
        log.info("Instantiating config object...")
        log.debug("Config file: %s", conf)

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
        '''Entrypoint, calls methods to set up node at boot. Runs automatically
        when class instantiated unless delay_setup arg passed (unit tests).
        '''

        # Connect to wifi, hit APIs for current time, sunrise/sunset timestamps
        self.api_calls()

        # Instantiate each config in self.device_configs and self.sensor_configs as
        # appropriate class, add to self.devices and self.sensors respectively
        self.instantiate_peripherals()

        # Create timers for all schedule rules expiring in next 24 hours
        self.build_queue()

        # Map relationships between sensors ("triggers") and devices ("targets")
        # Must run after build_queue to prevent sensors turning devices on/off
        # before correct scheduled rule applied
        self.build_groups()

        # Start timer to re-build schedule rule queue for next 24 hours around 3 am
        self.start_reload_schedule_rules_timer()

        log.info("Finished instantiating config")

    def start_reload_schedule_rules_timer(self):
        '''Schedules callback timer for a random time between 3:00-4:00 am.
        Updates sunrise/sunset times, regenerates schedule rule epoch times for
        next day, and creates callback timer for each scheduled rule change.
        '''

        # Get current epoch time + time tuple
        epoch = time.mktime(time.localtime())
        now = time.localtime(epoch)

        # Get epoch time of 3:00 am tomorrow
        # Only needed to increment day, other parameters roll over correctly in testing
        # Timezone set to none (final arg), required for compatibility with cpython test environment
        next_reload = time.mktime((now[0], now[1], now[2] + 1, 3, 0, 0, now[6], now[7], -1))

        # Calculate milliseconds until reload, add random 0-60 minute delay to stagger API calls
        adjust = randrange(3600)
        ms_until_reload = (next_reload - epoch + adjust) * 1000

        # Get HH:MM timestamp of next reload, write to log
        self.reload_time = f"{time.localtime(next_reload + adjust)[3]}:{time.localtime(next_reload + adjust)[4]}"
        log.info("Reload_schedule_rules callback scheduled for %s am", self.reload_time)

        # Add timer to queue
        SoftwareTimer.timer.create(ms_until_reload, self.reload_schedule_rules, "reload_schedule_rules")

    def instantiate_peripherals(self):
        '''Populates self.devices and self.sensors lists by instantiating
        config sections from self.device_configs and self.sensor_configs.
        Can only be called once on startup.
        '''

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
                self.ir_blaster_config["target"]
            )
            del self.ir_blaster_config

        # Delete device and sensor config dicts
        del self.device_configs
        del self.sensor_configs
        gc.collect()

    def instantiate_devices(self, conf):
        '''Takes dict with device IDs (device1, device2, etc) as keys, device
        config dicts as values. Instantiates appropriate hardware driver class
        with params for each device and adds instance to self.devices list.
        '''
        log.debug("Instantiating devices")
        for device in sorted(conf):
            # Add device's schedule rules to dict
            self.schedule[device] = conf[device]["schedule"]

            try:
                # Instantiate device with appropriate class
                instance = instantiate_hardware(device, **conf[device])

                # Add instance to config.devices
                self.devices.append(instance)
            except AttributeError:
                log.critical(
                    "Failed to instantiate %s (%s), params: %s",
                    device, conf[device]['_type'], conf[device]
                )
                print_with_timestamp(f"ERROR: Failed to instantiate {device} ({conf[device]['_type']}")
                pass
            except ValueError:
                log.critical(
                    "Failed to instantiate %s, unsupported device type %s",
                    device, conf[device]['_type']
                )
                print_with_timestamp(f"ERROR: Failed to instantiate {device}, unsupported device type {conf[device]['_type']}")

        log.debug("Finished instantiating device instances")

    def instantiate_sensors(self, conf):
        '''Takes dict with sensor IDs (sensor1, sensor2, etc) as keys, sensor
        config dicts as values. Instantiates appropriate hardware driver class
        with params for each sensor and adds instance to self.sensors list.
        '''
        log.debug("Instantiating sensors")
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
                log.critical(
                    "Failed to instantiate %s (%s), params: %s",
                    sensor, conf[sensor]['_type'], conf[sensor]
                )
                print_with_timestamp(f"ERROR: Failed to instantiate {sensor} ({conf[sensor]['_type']}")
                pass
            except ValueError:
                log.critical(
                    "Failed to instantiate %s, unsupported sensor type %s",
                    sensor, conf[sensor]['_type']
                )
                print_with_timestamp(f"ERROR: Failed to instantiate {sensor}, unsupported sensor type {conf[sensor]['_type']}")

        log.debug("Finished instantiating sensor instances")

    def build_groups(self):
        '''Maps relationships between sensors (triggers) and devices (targets).
        Multiple sensors with identical targets are merged into a single Group
        instance (can also contain 1 sensor with 1 or more target). Groups will
        check condition of all sensors when refresh method is called and turn
        devices on or off when conditions change.
        '''
        log.debug("Building groups")

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

        log.debug("Finished building %s groups", len(self.groups))

    def get_status(self):
        '''Returns dict with metadata and current status of all devices and
        sensors. Called by status API endpoint, frontend polls every 5 seconds
        and uses response to update react state.
        '''

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

    def api_calls(self):
        '''Connects to wifi (if not connected), sets system clock and
        sunrise/sunset times with values received from API.
        '''

        # Auto-reboot if startup doesn't complete in 1 min (prevents API calls
        # hanging, timer canceled at bottom of function once calls complete).
        reboot_timer.init(period=60000, mode=Timer.ONE_SHOT, callback=reboot)

        # Turn onboard LED on, indicates setup in progress
        led = Pin(2, Pin.OUT, value=1)

        # Connect to wifi
        wlan = network.WLAN(network.WLAN.IF_STA)
        wlan.active(True)
        if not wlan.isconnected():
            credentials = read_wifi_credentials_from_disk()
            log.debug("Attempting to connect to %s", credentials['ssid'])
            wlan.connect(credentials["ssid"], credentials["password"])

            # Wait until finished connecting before proceeding
            while not wlan.isconnected():
                continue
            else:
                print_with_timestamp(f"Successfully connected to {credentials['ssid']}")
                log.debug("Successfully connected to %s", credentials['ssid'])

        failed_attempts = 0

        # Ensure enough free ram for API response
        gc.collect()

        # Set system clock and sunrise/sunset times with timestamps from ipgeo API
        # Determines timezone by IP address unless config file contains GPS coords
        # Retry up to 5 times if API call fails, reboot after 5th failure
        while True:
            try:
                log.debug("Getting system time from ipgeolocation.io API...")
                # Use GPS coordinates if present, otherwise rely on IP lookup
                url = f"https://api.ipgeolocation.io/astronomy?apiKey={ipgeo_key}"
                if self.gps:
                    log.debug("Using GPS coordinates from config file")
                    url += f"&lat={self.gps['lat']}&long={self.gps['lon']}"

                response = requests.get(url, timeout=5)

                # Parse time parameters
                hour, minute, second = response.json()["current_time"].split(":")
                second, millisecond = second.split(".")

                # Parse date parameters
                year, month, day = map(int, response.json()["date"].split("-"))

                # Set RTC (uses different parameter order than time.localtime)
                RTC().datetime((year, month, day, 0, int(hour), int(minute), int(second), int(millisecond)))
                log.debug("System clock set")

                # Set sunrise/sunset times
                self.schedule_keywords["sunrise"] = response.json()["sunrise"]
                self.schedule_keywords["sunset"] = response.json()["sunset"]
                log.debug(
                    "Received sunrise time = %s, sunset time = %s",
                    self.schedule_keywords["sunrise"],
                    self.schedule_keywords["sunset"]
                )
                response.close()
                break

            # Issue with response object
            except KeyError:
                print_with_timestamp(f'ERROR (ipgeolocation.io): {response.json()["message"]}')
                log.error('ERROR (ipgeolocation.io): %s', response.json()["message"])
                reboot()

            # Network issue
            except OSError:
                print_with_timestamp("Failed to set system time, retrying...")
                log.error("Failed to set system time, retrying...")
                failed_attempts += 1
                if failed_attempts > 5:
                    log.critical("Failed to set system time 5 times, reboot triggered")
                    reboot()
                time.sleep_ms(1500)  # If failed, wait 1.5 seconds before retrying
                gc.collect()  # Free up memory before retrying
                pass

        log.info("Finished API calls (timestamp may look weird due to system clock change)")

        # Stop timer once API calls finish
        reboot_timer.deinit()

        # Turn off LED to confirm setup completed successfully
        led.value(0)

    def convert_rules(self, rules):
        '''Takes dict of schedule rules with HH:MM timestamps, returns dict of
        same rules with unix epoch timestamps for next time rule should run.
        Called every day between 3-4 am (epoch times only work once).
        '''

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

    def build_queue(self):
        '''Iterates all devices and sensors, converts schedule rule HH:MM times
        to unix epoch times, creates callback timers to change rules at correct
        times, and sets correct current scheduled_rule for each instance.
        '''
        log.debug("Building schedule rule queue for all devices and sensors")

        # Delete all existing schedule rule timers to avoid conflicts
        SoftwareTimer.timer.cancel("scheduler")

        for i in self.schedule:
            # Convert HH:MM timestamps to unix epoch timestamp of next run
            # Use copy to avoid overwriting schedule keywords with HH:MM in original
            rules = self.convert_rules(self.schedule[i].copy())

            # Get target instance (skip if unable to find)
            instance = self.find(i)
            if not instance:
                continue

            # No rules: set default_rule as scheduled_rule, skip to next instance
            if len(rules) == 0:
                # Set current_rule and scheduled_rule (returns False if invalid)
                if not instance.set_rule(instance.default_rule, True):
                    # If default_rule invalid, disable instance to prevent unpredictable behavior
                    log.critical(
                        "%s invalid default rule (%s), disabling instance",
                        instance.name, instance.default_rule
                    )
                    instance.current_rule = "disabled"
                    instance.scheduled_rule = "disabled"
                    instance.default_rule = "disabled"
                    instance.disable()
                continue

            # Get list of timestamps, sort chronologically
            # First item in queue is current scheduled rule
            queue = []
            for j in rules:
                queue.append(j)
            queue.sort()

            # Set first item as current_rule and scheduled_rule (returns False if invalid)
            if not instance.set_rule(rules[queue.pop(0)], True):
                # Fall back to default_rule if scheduled rule is invalid
                log.error(
                    "%s scheduled rule failed validation, falling back to default rule",
                    instance.name
                )
                if not instance.set_rule(instance.default_rule, True):
                    # If both  rules invalid, disable instance to prevent unpredictable behavior
                    log.critical(
                        "%s invalid default rule (%s), disabling instance",
                        instance.name, instance.default_rule
                    )
                    instance.current_rule = "disabled"
                    instance.scheduled_rule = "disabled"
                    instance.default_rule = "disabled"
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
                milliseconds = (k - epoch) * 1000
                SoftwareTimer.timer.create(milliseconds, instance.next_rule, "scheduler")
                gc.collect()

        print_with_timestamp("Finished building schedule rule queue")
        log.debug("Finished building queue, total timers = %s", len(SoftwareTimer.timer.queue))

    def find(self, target):
        '''Takes ID (device1, sensor2, etc), returns instance or False.'''
        if is_device(target):
            for i in self.devices:
                if i.name == target:
                    return i
            else:
                log.debug("Config.find: Unable to find %s", target)
                return False

        elif is_sensor(target):
            for i in self.sensors:
                if i.name == target:
                    return i
            else:
                log.debug("Config.find: Unable to find %s", target)
                return False

        else:
            log.debug("Config.find: Unable to find %s", target)
            return False

    def reload_schedule_rules(self):
        '''Called by timer between 3-4 am every day, updates sunrise/sunset
        times and generates schedule rule epoch timestamps for next day.
        '''
        print_with_timestamp("Reloading schedule rules...")
        log.info("Callback: Reloading schedule rules")
        # Get up-to-date sunrise/sunset, set system clock (in case of daylight savings)
        self.api_calls()

        # Create timers for all schedule rules expiring in next 24 hours
        self.build_queue()

        # Set timer to run again tomorrow between 3-4 am
        self.start_reload_schedule_rules_timer()
