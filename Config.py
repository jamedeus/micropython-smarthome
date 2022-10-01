import network
import time
from machine import Pin, Timer, RTC
import urequests
import json
from random import randrange
import uasyncio as asyncio
import logging
import gc
import SoftwareTimer
from Group import Group

# Set name for module's log lines
log = logging.getLogger("Config")

# Timer re-runs startup every day at 3:00 am (reload schedule rules, sunrise/sunset times, etc)
config_timer = Timer(1)
# Used to reboot if startup hangs for longer than 1 minute
reboot_timer = Timer(2)

# Turn onboard LED on, indicates setup in progress
led = Pin(2, Pin.OUT, value=1)



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

        # Call function to connect to wifi + hit APIs
        self.api_calls()

        # Tells loop when it is time to re-run API calls + build schedule rule queue
        self.reload_rules = False

        # Dictionairy holds schedule rules for all devices and sensors
        self.schedule = {}

        # Create empty list, will contain instances for each device
        self.devices = []

        # Iterate json
        for device in conf:
            if not device.startswith("device"): continue

            # Add device's schedule rules to dict
            self.schedule[device] = conf[device]["schedule"]

            # Instantiate each device as appropriate class
            if conf[device]["type"] == "dimmer" or conf[device]["type"] == "bulb":
                from Tplink import Tplink
                instance = Tplink( device, conf[device]["nickname"], conf[device]["type"], True, None, conf[device]["default_rule"], conf[device]["ip"] )

            elif conf[device]["type"] == "relay":
                from Relay import Relay
                instance = Relay( device, conf[device]["nickname"], conf[device]["type"], True, None, conf[device]["default_rule"], conf[device]["ip"] )

            elif conf[device]["type"] == "dumb-relay":
                from DumbRelay import DumbRelay
                instance = DumbRelay( device, conf[device]["nickname"], conf[device]["type"], True, None, conf[device]["default_rule"], int(conf[device]["pin"]) )

            elif conf[device]["type"] == "desktop":
                from Desktop_target import Desktop_target
                instance = Desktop_target( device, conf[device]["nickname"], conf[device]["type"], True, None, conf[device]["default_rule"], conf[device]["ip"] )

            elif conf[device]["type"] == "pwm":
                from LedStrip import LedStrip
                instance = LedStrip( device, conf[device]["nickname"], conf[device]["type"], True, None, conf[device]["default_rule"], int(conf[device]["pin"]), conf[device]["min"], conf[device]["max"] )

            elif conf[device]["type"] == "mosfet":
                from Mosfet import Mosfet
                instance = Mosfet( device, conf[device]["nickname"], conf[device]["type"], True, None, conf[device]["default_rule"], int(conf[device]["pin"]) )

            elif conf[device]["type"] == "api-target":
                from ApiTarget import ApiTarget
                instance = ApiTarget( device, conf[device]["nickname"], conf[device]["type"], True, None, conf[device]["default_rule"], conf[device]["ip"] )

            # Add instance to config.devices
            self.devices.append(instance)

        # Can only have 1 instance (driver limitation)
        # Since IR has no schedule and is only triggered by API, doesn't make sense to subclass or add to self.devices
        if "ir_blaster" in conf:
            from IrBlaster import IrBlaster
            self.ir_blaster = IrBlaster( int(conf["ir_blaster"]["pin"]), conf["ir_blaster"]["target"] )

        log.debug("Finished creating device instances")

        # Create empty list, will contain instances for each sensor
        self.sensors = []

        for sensor in conf:
            if not sensor.startswith("sensor"): continue

            # Add sensor's schedule rules to dict
            self.schedule[sensor] = conf[sensor]["schedule"]

            # Add class instance as dict key, enabled bool as value (allows sensor to skip disabled targets)
            targets = []
            for target in conf[sensor]["targets"]:
                targets.append(self.find(target))

            # Instantiate sensor as appropriate class
            if conf[sensor]["type"] == "pir":
                from MotionSensor import MotionSensor
                instance = MotionSensor(sensor, conf[sensor]["nickname"], conf[sensor]["type"], True, None, conf[sensor]["default_rule"], targets, int(conf[sensor]["pin"]))

            elif conf[sensor]["type"] == "desktop":
                from Desktop_trigger import Desktop_trigger
                instance = Desktop_trigger(sensor, conf[sensor]["nickname"], conf[sensor]["type"], True, None, conf[sensor]["default_rule"], targets, conf[sensor]["ip"])

            elif conf[sensor]["type"] == "si7021":
                from Thermostat import Thermostat
                instance = Thermostat(sensor, conf[sensor]["nickname"], conf[sensor]["type"], True, int(conf[sensor]["default_rule"]), conf[sensor]["default_rule"], conf[sensor]["mode"], conf[sensor]["tolerance"], targets)

            elif conf[sensor]["type"] == "dummy":
                from Dummy import Dummy
                instance = Dummy(sensor, conf[sensor]["nickname"], conf[sensor]["type"], True, None, conf[sensor]["default_rule"], targets)

            elif conf[sensor]["type"] == "switch":
                from Switch import Switch
                instance = Switch(sensor, conf[sensor]["nickname"], conf[sensor]["type"], True, None, conf[sensor]["default_rule"], targets, int(conf[sensor]["pin"]))

            # Add the sensor instance to each of it's target's "triggered_by" list
            for t in targets:
                t.triggered_by.append(instance)

            # Add instance to config.sensors
            self.sensors.append(instance)

        log.debug("Finished creating sensor instances")

        # Create timers for all schedule rules expiring in next 24 hours
        self.build_queue()

        # Map relationships between sensors ("triggers") and devices ("targets")
        # If multiple sensors have identical targets, they will be merged into a "group". Otherwise, group is created for each sensor.
        # Iterated by main loop in boot.py
        self.build_groups()

        # Get epoch time of next 3:00 am (re-build schedule rule queue for next 24 hours)
        epoch = time.mktime(time.localtime())
        now = time.localtime(epoch)
        if now[3] < 2:
            next_reset = time.mktime((now[0], now[1], now[2], 3, 0, 0, now[6], now[7]))
        else:
            next_reset = time.mktime((now[0], now[1], now[2]+1, 3, 0, 0, now[6], now[7])) # In testing, only needed to increment day - other parameters roll over correctly

        # Set timer to reload schedule rules at a random time between 3-4 am (prevent multiple nodes hitting API at same second)
        adjust = randrange(3600)
        log.debug(f"Reload_schedule_rules callback scheduled for {time.localtime(next_reset + adjust)[3]}:{time.localtime(next_reset + adjust)[4]} am")
        next_reset = (next_reset - epoch + adjust) * 1000
        config_timer.init(period=next_reset, mode=Timer.ONE_SHOT, callback=self.reload_schedule_rules)

        log.info("Finished instantiating config")



    def get_status(self):
        status_dict = {}
        status_dict["metadata"] = {}
        status_dict["metadata"]["id"] = self.identifier
        status_dict["metadata"]["floor"] = self.floor
        status_dict["metadata"]["location"] = self.location
        if "ir_blaster" in self.__dict__:
            status_dict["metadata"]["ir_blaster"] = True
        else:
            status_dict["metadata"]["ir_blaster"] = False

        status_dict["devices"] = {}
        for i in self.devices:
            status_dict["devices"][i.name] = {}
            status_dict["devices"][i.name]["nickname"] = i.nickname
            status_dict["devices"][i.name]["type"] = i.device_type
            status_dict["devices"][i.name]["enabled"] = i.enabled
            status_dict["devices"][i.name]["current_rule"] = i.current_rule
            status_dict["devices"][i.name]["scheduled_rule"] = i.scheduled_rule
            status_dict["devices"][i.name]["turned_on"] = i.state
            status_dict["devices"][i.name]["schedule"] = self.schedule[i.name]

        status_dict["sensors"] = {}
        for i in self.sensors:
            status_dict["sensors"][i.name] = {}
            status_dict["sensors"][i.name]["nickname"] = i.nickname
            status_dict["sensors"][i.name]["type"] = i.sensor_type
            status_dict["sensors"][i.name]["enabled"] = i.enabled
            status_dict["sensors"][i.name]["current_rule"] = i.current_rule
            status_dict["sensors"][i.name]["condition_met"] = i.condition_met()
            status_dict["sensors"][i.name]["scheduled_rule"] = i.scheduled_rule
            status_dict["sensors"][i.name]["targets"] = []
            for t in i.targets:
                status_dict["sensors"][i.name]["targets"].append(t.name)
            status_dict["sensors"][i.name]["schedule"] = self.schedule[i.name]

            # If node has temp sensor, add climate data
            if i.sensor_type == "si7021":
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
        if not wlan.isconnected(): wlan.connect(self.credentials[0], self.credentials[1])

        # Wait until finished connecting before proceeding
        while not wlan.isconnected():
            continue
        else:
            print(f"Successfully connected to {self.credentials[0]}")
            log.info(f"Successfully connected to {self.credentials[0]}")

        failed_attempts = 0

        # Ensure enough free ram for API resopnse
        gc.collect()

        # Set current time from internet in correct timezone, retry until successful (note: ntptime is easier but doesn't support timezone)

        while True:
            try:
                response = urequests.get("https://api.ipgeolocation.io/timezone?apiKey=ddcf9be5a455453e99d84de3dfe825bc&tz=America/Los_Angeles")

                # Convert epoch (seconds since 01/01/1970 GMT) to micropython epoch (since 01/01/2000: -946684800 for 30 years, -28800 for PST timezone)
                mepoch = int(response.json()["date_time_unix"]) - 946713600

                # Epoch does not include daylight savings - adjust if needed
                if response.json()["is_dst"]:
                    mepoch += 3600

                # Get datetime object, set system clock
                now = time.localtime(mepoch)
                RTC().datetime((now[0], now[1], now[2], now[6], now[3], now[4], now[5], 0)) # RTC uses different parameter order
                response.close()
                break
            except:
                print("Failed setting system time, retrying...")
                log.debug("Failed setting system time, retrying...")
                failed_attempts += 1
                if failed_attempts > 5:
                    log.info("Failed to get system time 5 times, reboot triggered")
                    reboot()
                time.sleep_ms(1500) # If failed, wait 1.5 seconds before retrying
                gc.collect() # Free up memory before retrying
                pass

        log.debug("Successfully set system time")

        # Prevent no-mem error when API response received
        gc.collect()

        # Get sunrise/sunset time, retry until successful
        while True:
            try:
                response = urequests.get("https://api.ipgeolocation.io/astronomy?apiKey=ddcf9be5a455453e99d84de3dfe825bc&lat=45.524722&long=-122.6771891")
                # Parse out sunrise/sunset, convert to 24h format
                self.sunrise = response.json()["sunrise"]
                self.sunset = response.json()["sunset"]
                response.close()
                break # Break loop once request succeeds
            except:
                print("Failed getting sunrise/sunset time, retrying...")
                log.debug("Failed getting sunrise/sunset time, retrying...")
                failed_attempts += 1
                if failed_attempts > 5:
                    log.info("Failed to get sunrise/sunset time 5 times, reboot triggered")
                    reboot()
                time.sleep_ms(1500) # If failed, wait 1.5 seconds before retrying
                gc.collect() # Free up memory before retrying
                pass # Allow loop to continue

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

        # Check for sunrise/sunet rules, replace "sunrise"/"sunset" with today's timestamps (converted to epoch time in loop below)
        if "sunrise" in rules:
            rules[self.sunrise] = rules["sunrise"]
            del rules["sunrise"]
        if "sunset" in rules:
            rules[self.sunset] = rules["sunset"]
            del rules["sunset"]

        # Get rule start times, sort chronologically
        schedule = list(rules)
        schedule.sort()

        # Get epoch time in current timezone
        epoch = time.mktime(time.localtime())
        # Get time tuple in current timezone
        now = time.localtime(epoch)

        for rule in schedule:
            # Returns epoch time of rule, uses all current parameters but substitutes hour + min from schedule and 0 for seconds
            trigger_time = time.mktime((now[0], now[1], now[2], int(rule.split(":")[0]), int(rule.split(":")[1]), 0, now[6], now[7]))

            # Add to results: Key = unix timestamp, value = value from original rules dict
            result[trigger_time] = rules[rule]
            # Also add same rule with timestamp 24 hours earlier (ensures there are expired rules so possible to find currently-active rule)
            result[trigger_time-86400] = rules[rule]
            # Also add same rule with timestamp 24 hours later (moves rules that have already expired today to tomorrow)
            result[trigger_time+86400] = rules[rule]

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
            rules = self.convert_rules(self.schedule[i])

            # Get target instance
            instance = self.find(i)

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

            # Set target's current_rule (set_rule method passes to syntax validator, returns True if valid, False if not)
            if instance.set_rule(rules[queue.pop(0)]):
                # If rule valid, set as scheduled_rule
                instance.scheduled_rule = instance.current_rule
            else:
                # If rule is invalid, fall back to default rule
                log.error(f"{instance.name} scheduled rule failed validation, falling back to default rule")
                if instance.set_rule(instance.default_rule):
                    instance.scheduled_rule = instance.current_rule
                else:
                    # If both scheduled and default rules are invalid, disable instance to prevent unpredictable behavior
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
        if target.startswith("device"):
            for i in self.devices:
                if i.name == target:
                    return i
            else:
                log.debug(f"Config.find: Unable to find {target}")
                return False

        elif target.startswith("sensor"):
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
                next_reset = time.mktime((now[0], now[1], now[2]+1, 3, 0, 0, now[6], now[7]))
                adjust = randrange(3600)
                log.debug(f"Reload_schedule_rules callback scheduled for {time.localtime(next_reset + adjust)[3]}:{time.localtime(next_reset + adjust)[4]} am")
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
