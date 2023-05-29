import network
import time
from machine import Pin, Timer, RTC
import urequests
from random import randrange
import uasyncio as asyncio
import logging
import gc
import re
import SoftwareTimer
from Group import Group
from util import is_device, is_sensor, is_device_or_sensor

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
        "relay": "Relay",
        "dumb-relay": "DumbRelay",
        "desktop": "Desktop_target",
        "pwm": "LedStrip",
        "mosfet": "Mosfet",
        "api-target": "ApiTarget",
        "wled": "Wled"
    },
    "sensors": {
        "pir": "MotionSensor",
        "desktop": "Desktop_trigger",
        "dummy": "Dummy",
        "si7021": "Thermostat",
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


class Config():
    def __init__(self, conf):
        print("\nInstantiating config object...\n")
        log.info("Instantiating config object...")
        log.debug(f"Config file: {conf}")

        # Load wifi credentials tuple
        self.credentials = (conf["wifi"]["ssid"], conf["wifi"]["password"])

        # Load metadata parameters - (unused so far)
        self.identifier = conf["metadata"]["id"]
        self.location = conf["metadata"]["location"]
        self.floor = conf["metadata"]["floor"]

        # Tells loop when it is time to re-run API calls + build schedule rule queue
        self.reload_rules = False

        # Dictionairy holds schedule rules for all devices and sensors
        self.schedule = {}

        # Dictionairy of keyword-timestamp pairs, used for schedule rules
        self.schedule_keywords = {'sunrise': '00:00', 'sunset': '00:00'}
        self.schedule_keywords.update(conf["metadata"]["schedule_keywords"])

        # Call function to connect to wifi + hit APIs
        self.api_calls()

        # Create empty list, will contain instances for each device
        self.devices = []

        # Iterate json, instantiate devices
        for device in conf:
            if not is_device(device): continue

            # Add device's schedule rules to dict
            self.schedule[device] = conf[device]["schedule"]

            try:
                # Instantiate device with appropriate class
                instance = instantiate_hardware(device, **conf[device])

                # Add instance to config.devices
                self.devices.append(instance)
            except AttributeError:
                log.critical(f"Failed to instantiate {device}: type = {conf[device]['_type']}, default_rule = {conf[device]['default_rule']}")
                print(f"Failed to instantiate {device}: type = {conf[device]['_type']}, default_rule = {conf[device]['default_rule']}")
                pass
            except ValueError:
                log.critical(f"Failed to instantiate {device}, unsupported device type {conf[device]['_type']}")
                print(f"Failed to instantiate {device}, unsupported device type {conf[device]['_type']}")

        # Can only have 1 instance (driver limitation)
        # Since IR has no schedule and is only triggered by API, doesn't make sense to subclass or add to self.devices
        if "ir_blaster" in conf:
            from IrBlaster import IrBlaster
            self.ir_blaster = IrBlaster(int(conf["ir_blaster"]["pin"]), conf["ir_blaster"]["target"])

        log.debug("Finished creating device instances")

        # Create empty list, will contain instances for each sensor
        self.sensors = []

        for sensor in conf:
            if not is_sensor(sensor): continue

            # Add sensor's schedule rules to dict
            self.schedule[sensor] = conf[sensor]["schedule"]

            try:
                # Add class instance as dict key, enabled bool as value (allows sensor to skip disabled targets)
                targets = []

                # Find instances for each device ID in targets list
                for target in conf[sensor]["targets"]:
                    t = self.find(target)
                    # Only add if instance found (instantiation may have failed due to invalid config params)
                    if t:
                        targets.append(t)

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
                log.critical(f"Failed to instantiate {sensor}: type = {conf[sensor]['_type']}, default_rule = {conf[sensor]['default_rule']}")
                print(f"Failed to instantiate {sensor}: type = {conf[sensor]['_type']}, default_rule = {conf[sensor]['default_rule']}")
                pass
            except ValueError:
                log.critical(f"Failed to instantiate {sensor}, unsupported sensor type {conf[sensor]['_type']}")
                print(f"Failed to instantiate {sensor}, unsupported sensor type {conf[sensor]['_type']}")

        log.debug("Finished creating sensor instances")

        # Create timers for all schedule rules expiring in next 24 hours
        self.build_queue()

        # Map relationships between sensors ("triggers") and devices ("targets")
        # Multiple sensors with identical targets are merged into groups (or 1 sensor per group if unique targets)
        # Groups iterated by main loop in boot.py, methods used to check conditions and apply actions
        self.build_groups()

        # Get epoch time of next 3:00 am (re-build schedule rule queue for next 24 hours)
        epoch = time.mktime(time.localtime())
        now = time.localtime(epoch)
        if now[3] < 2:
            next_reset = time.mktime((now[0], now[1], now[2], 3, 0, 0, now[6], now[7]))
        else:
            # In testing, only needed to increment day - other parameters roll over correctly
            next_reset = time.mktime((now[0], now[1], now[2] + 1, 3, 0, 0, now[6], now[7]))

        # Reload schedule rules at random time between 3-4 am (prevent multiple nodes hitting API at same second)
        adjust = randrange(3600)
        reset_timestamp = f"{time.localtime(next_reset + adjust)[3]}:{time.localtime(next_reset + adjust)[4]}"
        log.debug(f"Reload_schedule_rules callback scheduled for {reset_timestamp} am")
        next_reset = (next_reset - epoch + adjust) * 1000
        config_timer.init(period=next_reset, mode=Timer.ONE_SHOT, callback=self.reload_schedule_rules)

        log.info("Finished instantiating config")

    def get_status(self):
        status_dict = {}
        status_dict["metadata"] = {}
        status_dict["metadata"]["id"] = self.identifier
        status_dict["metadata"]["floor"] = self.floor
        status_dict["metadata"]["location"] = self.location
        status_dict["metadata"]["schedule_keywords"] = self.schedule_keywords
        if "ir_blaster" in self.__dict__:
            status_dict["metadata"]["ir_blaster"] = True
        else:
            status_dict["metadata"]["ir_blaster"] = False

        status_dict["devices"] = {}
        for i in self.devices:
            status_dict["devices"][i.name] = {}
            status_dict["devices"][i.name]["nickname"] = i.nickname
            status_dict["devices"][i.name]["type"] = i._type
            status_dict["devices"][i.name]["enabled"] = i.enabled
            status_dict["devices"][i.name]["current_rule"] = i.current_rule
            status_dict["devices"][i.name]["scheduled_rule"] = i.scheduled_rule
            status_dict["devices"][i.name]["turned_on"] = i.state
            status_dict["devices"][i.name]["schedule"] = self.schedule[i.name]

            # If device is PWM, add min/max
            if i._type == "pwm":
                status_dict["devices"][i.name]["min"] = i.min_bright
                status_dict["devices"][i.name]["max"] = i.max_bright

        status_dict["sensors"] = {}
        for i in self.sensors:
            status_dict["sensors"][i.name] = {}
            status_dict["sensors"][i.name]["nickname"] = i.nickname
            status_dict["sensors"][i.name]["type"] = i._type
            status_dict["sensors"][i.name]["enabled"] = i.enabled
            status_dict["sensors"][i.name]["current_rule"] = i.current_rule
            status_dict["sensors"][i.name]["condition_met"] = i.condition_met()
            status_dict["sensors"][i.name]["scheduled_rule"] = i.scheduled_rule
            status_dict["sensors"][i.name]["targets"] = []
            for t in i.targets:
                status_dict["sensors"][i.name]["targets"].append(t.name)
            status_dict["sensors"][i.name]["schedule"] = self.schedule[i.name]

            # If node has temp sensor, add climate data
            if i._type == "si7021":
                status_dict["sensors"][i.name]["temp"] = i.fahrenheit()
                status_dict["sensors"][i.name]["humid"] = i.temp_sensor.relative_humidity

        return status_dict

    def api_calls(self):
        # Auto-reboot if startup doesn't complete in 1 min (prevents API calls hanging, canceled at bottom of function)
        reboot_timer.init(period=60000, mode=Timer.ONE_SHOT, callback=reboot)

        # Turn onboard LED on, indicates setup in progress
        led = Pin(2, Pin.OUT, value=1)

        log.debug(f"Attempting to connect to {self.credentials[0]}")

        # Connect to wifi
        wlan = network.WLAN(network.STA_IF)
        wlan.active(True)
        if not wlan.isconnected():
            wlan.connect(self.credentials[0], self.credentials[1])

        # Wait until finished connecting before proceeding
        while not wlan.isconnected():
            continue
        else:
            print(f"Successfully connected to {self.credentials[0]}")
            log.info(f"Successfully connected to {self.credentials[0]}")

        failed_attempts = 0

        # Ensure enough free ram for API resopnse
        gc.collect()

        # Set time from internet in correct timezone, retry until successful (ntptime easier but no timezone support)
        while True:
            try:
                response = urequests.get("https://api.ipgeolocation.io/timezone?apiKey=ddcf9be5a455453e99d84de3dfe825bc&tz=America/Los_Angeles")

                # Convert epoch (seconds since 01/01/1970 GMT) to micropython epoch (since 01/01/2000)
                # -946684800 for 30 years, -28800 for PST timezone)
                mepoch = int(response.json()["date_time_unix"]) - 946713600

                # Epoch does not include daylight savings - adjust if needed
                if response.json()["is_dst"]:
                    mepoch += 3600

                # Get datetime object, set system clock
                now = time.localtime(mepoch)
                # RTC uses different parameter order
                RTC().datetime((now[0], now[1], now[2], now[6], now[3], now[4], now[5], 0))
                response.close()
                break
            except:
                print("Failed setting system time, retrying...")
                log.debug("Failed setting system time, retrying...")
                failed_attempts += 1
                if failed_attempts > 5:
                    log.info("Failed to get system time 5 times, reboot triggered")
                    reboot()
                time.sleep_ms(1500)  # If failed, wait 1.5 seconds before retrying
                gc.collect()  # Free up memory before retrying
                pass

        log.debug("Successfully set system time")

        # Prevent no-mem error when API response received
        gc.collect()

        # Get sunrise/sunset time, retry until successful
        while True:
            try:
                response = urequests.get("https://api.ipgeolocation.io/astronomy?apiKey=ddcf9be5a455453e99d84de3dfe825bc&lat=45.524722&long=-122.6771891")
                # Parse out sunrise/sunset, convert to 24h format
                self.schedule_keywords["sunrise"] = response.json()["sunrise"]
                self.schedule_keywords["sunset"] = response.json()["sunset"]
                response.close()
                break  # Break loop once request succeeds
            except:
                print("Failed getting sunrise/sunset time, retrying...")
                log.debug("Failed getting sunrise/sunset time, retrying...")
                failed_attempts += 1
                if failed_attempts > 5:
                    log.info("Failed to get sunrise/sunset time 5 times, reboot triggered")
                    reboot()
                time.sleep_ms(1500)  # If failed, wait 1.5 seconds before retrying
                gc.collect()  # Free up memory before retrying
                pass  # Allow loop to continue

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
            time_tuple = (now[0], now[1], now[2], int(rule.split(":")[0]), int(rule.split(":")[1]), 0, now[6], now[7])
            trigger_time = time.mktime(time_tuple)

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
                    log.critical(f"{instance.name} default rule ({instance.default_rule}) failed validation, instance will be disabled")
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
                    log.critical(f"{instance.name} default rule ({instance.default_rule}) failed validation, instance will be disabled")
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

        print(f"Finished building queue, total timers = {len(SoftwareTimer.timer.queue)}")
        log.debug(f"Finished building queue, total timers = {len(SoftwareTimer.timer.queue)}")

    def build_groups(self):
        # Stores relationships between sensors ("triggers") and devices ("targets"), iterated by main loop
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
    def reload_schedule_rules(self, t):
        self.reload_rules = True

    # Loop re-builds schedule rule queue when config_timer expires
    async def loop(self):
        while True:
            # Set to True by timer every night between 3-4 am
            if self.reload_rules:
                print("Reloading schedule rules...")
                log.info("3:00 am callback, reloading schedule rules...")
                # Get up-to-date sunrise/sunset, set system clock (in case of daylight savings)
                self.api_calls()

                # Create timers for all schedule rules expiring in next 24 hours
                self.build_queue()

                self.reload_rules = False

                # Set timer to run again tomorrow between 3-4 am
                epoch = time.mktime(time.localtime())
                now = time.localtime(epoch)
                next_reset = time.mktime((now[0], now[1], now[2] + 1, 3, 0, 0, now[6], now[7]))
                adjust = randrange(3600)
                callback_time = f"{time.localtime(next_reset + adjust)[3]}:{time.localtime(next_reset + adjust)[4]}"
                log.debug(f"Reload_schedule_rules callback scheduled for {callback_time} am")
                next_reset = (next_reset - epoch + adjust) * 1000
                config_timer.init(period=next_reset, mode=Timer.ONE_SHOT, callback=self.reload_schedule_rules)

            else:
                # Check every minute
                await asyncio.sleep(60)


def reboot(arg="unused"):
    print("Reboot function called, rebooting...")
    log.info("Reboot function called, rebooting...\n")
    from machine import reset
    reset()
