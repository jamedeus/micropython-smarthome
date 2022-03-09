import network
import time
from machine import Pin, Timer, RTC
import urequests
import json
import os
from random import randrange
import uasyncio as asyncio
import logging
import gc

# Set log file and syntax
logging.basicConfig(level=logging.INFO, filename='app.log', format='%(asctime)s - %(levelname)s - %(name)s - %(message)s', style='%')
log = logging.getLogger("Config")

# Timer re-runs startup every day at 3:00 am (reload schedule rules, sunrise/sunset times, etc)
config_timer = Timer(1)
# Used to reboot if startup hangs for longer than 1 minute
reboot_timer = Timer(2)
# Used when it is time to switch to the next schedule rule
next_rule_timer = Timer(3)

# Turn onboard LED on, indicates setup in progress
led = Pin(2, Pin.OUT, value=1)



class Config():
    def __init__(self, conf):
        print("\nInstantiating config object...\n")
        log.info("Instantiating config object...")

        # Load wifi credentials tuple
        self.credentials = (conf["wifi"]["ssid"], conf["wifi"]["password"])

        # Load metadata parameters - (unused so far)
        self.identifier = conf["metadata"]["id"]
        self.location = conf["metadata"]["location"]
        self.floor = conf["metadata"]["floor"]

        # Call function to connect to wifi + hit APIs
        self.api_calls()

        # Create empty dictionairy, will contain sub-dict for each device
        self.devices = {}

        # Iterate json
        for device in conf:
            if not device.startswith("device"): continue

            # Instantiate each device as appropriate class
            if conf[device]["type"] == "dimmer" or conf[device]["type"] == "bulb":
                from Tplink import Tplink
                instance = Tplink( device, conf[device]["type"], True, None, None, conf[device]["ip"] )

            elif conf[device]["type"] == "relay" or conf[device]["type"] == "desktop":
                from Relay import Relay
                instance = Relay( device, conf[device]["type"], True, None, None, conf[device]["ip"] )

            elif conf[device]["type"] == "pwm":
                from LedStrip import LedStrip
                instance = LedStrip( device, conf[device]["type"], True, None, None, conf[device]["pin"], conf[device]["min"], conf[device]["max"] )

            # Add to config.devices dict with class object as key + json sub-dict as value
            self.devices[instance] = conf[device]

            # Overwrite schedule section with unix timestamp rules
            try:
                self.devices[instance]["schedule"] = self.convert_rules(conf[device]["schedule"])
            except KeyError:
                pass # Skip devices with no schedule section

        # Can only have 1 instance (driver limitation)
        # Since IR has no schedule and is only triggered by API, doesn't make sense to subclass or add to self.devices
        if "ir_blaster" in conf:
            from IrBlaster import IrBlaster
            self.ir_blaster = IrBlaster( conf["ir_blaster"]["pin"], conf["ir_blaster"]["target"] )

        log.debug("Finished creating device instances")

        # Create empty dictionairy, will contain sub-dict for each sensor
        self.sensors = {}

        for sensor in conf:
            if not sensor.startswith("sensor"): continue

            # Add class instance as dict key, enabled bool as value (allows sensor to skip disabled targets)
            targets = {}
            for target in conf[sensor]["targets"]:
                t = self.find(target)
                targets[t] = t.enabled

            # Instantiate sensor as appropriate class
            if conf[sensor]["type"] == "pir":
                from MotionSensor import MotionSensor
                instance = MotionSensor(sensor, conf[sensor]["type"], True, None, None, targets, conf[sensor]["pin"])

            elif conf[sensor]["type"] == "si7021":
                from Thermostat import Thermostat
                instance = Thermostat(sensor, conf[sensor]["type"], True, int(conf[sensor]["default_setting"]), conf[sensor]["default_setting"], targets)

            # Add the sensor instance to each of it's target's "triggered_by" list
            for t in targets:
                t.triggered_by.append(instance)

            # Add to config.sensors dict with class object as key + json sub-dict as value
            self.sensors[instance] = conf[sensor]
            # Overwrite schedule section with unix timestamp rules
            self.sensors[instance]["schedule"] = self.convert_rules(conf[sensor]["schedule"])

        log.debug("Finished creating sensor instances")

        self.rule_parser()

        # Get epoch time of next 3:00 am (re-run timestamp to epoch conversion)
        epoch = time.mktime(time.localtime())
        now = time.localtime(epoch)
        if now[3] < 3:
            next_reset = time.mktime((now[0], now[1], now[2], 3, 0, 0, now[6], now[7]))
        else:
            next_reset = time.mktime((now[0], now[1], now[2]+1, 3, 0, 0, now[6], now[7])) # In testing, only needed to increment day - other parameters roll over correctly

        # Set timer to reload schedule rules at a random time between 3-4 am (prevent multiple units hitting API at same second)
        next_reset = (next_reset - epoch + randrange(3600)) * 1000
        config_timer.init(period=next_reset, mode=Timer.ONE_SHOT, callback=reload_schedule_rules)

        log.info("Finished instantiating config")



    def get_status(self):
        status_dict = {}
        status_dict["metadata"] = {}
        status_dict["metadata"]["id"] = self.identifier
        status_dict["metadata"]["floor"] = self.floor
        status_dict["metadata"]["location"] = self.location

        status_dict["devices"] = {}
        for i in self.devices:
            status_dict["devices"][i.name] = {}
            status_dict["devices"][i.name]["type"] = i.device_type
            status_dict["devices"][i.name]["current_rule"] = i.current_rule

        status_dict["sensors"] = {}
        for i in self.sensors:
            status_dict["sensors"][i.name] = {}
            status_dict["sensors"][i.name]["type"] = i.sensor_type
            status_dict["sensors"][i.name]["current_rule"] = i.current_rule
            status_dict["sensors"][i.name]["targets"] = []
            for t in i.targets:
                status_dict["sensors"][i.name]["targets"].append(t.name)
                for q in status_dict["devices"]:
                    if q == t.name:
                        status_dict["devices"][q]["turned_on"] = i.state
            status_dict["sensors"][i.name]["enabled"] = i.enabled

        return status_dict



    def api_calls(self):
        # Auto-reboot if startup doesn't complete in 1 min (prevents API calls hanging, canceled at bottom of function)
        reboot_timer.init(period=60000, mode=Timer.ONE_SHOT, callback=reboot)

        # Turn onboard LED on, indicates setup in progress
        led = Pin(2, Pin.OUT, value=1)

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

        # Prevent no-mem error when API response received
        # TODO - Keep testing. This fixed all failures with try/except commented, but they happen again with try/except
        gc.collect()

        # Set current time from internet in correct timezone, retry until successful (note: ntptime is easier but doesn't support timezone)
        # TODO: Continue to optimize this - it seems to only fail when inside try/except (about 50% of the time), otherwise it always works...
        # Since RTC call will traceback if request fail, could just rely on reboot_timer to recover from failure
        while True:
            try:
                response = urequests.get("https://api.ipgeolocation.io/timezone?apiKey=ddcf9be5a455453e99d84de3dfe825bc&tz=America/Los_Angeles")
                now = time.localtime(int(response.json()["date_time_unix"]) - 946713600) # Convert unix epoch (from API) to micropython epoch (starts in 2000), then get time tuple
                RTC().datetime((now[0], now[1], now[2], now[6], now[3], now[4], now[5], 0)) # Set RTC - micropython is stupid and uses different parameter order for RTC
                response.close()
                break
            except:
                print("Failed setting system time, retrying...")
                log.info("Failed setting system time, retrying...")
                failed_attempts += 1
                if failed_attempts > 5: reboot()
                time.sleep_ms(1500) # If failed, wait 1.5 seconds before retrying
                gc.collect() # Free up memory before retrying
                pass

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
                log.info("Failed getting sunrise/sunset time, retrying...")
                failed_attempts += 1
                if failed_attempts > 5: reboot()
                time.sleep_ms(1500) # If failed, wait 1.5 seconds before retrying
                gc.collect() # Free up memory before retrying
                pass # Allow loop to continue

        log.info("Finished API calls...")

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
            # Also add a rule at the same time yesterday and tomorrow - temporary workaround for bug TODO - review this, see if there is a better approach
            result[trigger_time-86400] = rules[rule]
            result[trigger_time+86400] = rules[rule]

        # Return the finished dictionairy
        return result



    # Receive sub-dictionairy containing schedule rules, compare each against current time, return correct rule
    def rule_parser(self, arg="unused"):
        # Store timestamp of next rule, for callback timer
        next_rule = None

        items = {}

        for i in self.devices:
            try:
                items[i] = self.devices[i]["schedule"]
            except KeyError:
                pass # Skip devices with no schedule rules

        for i in self.sensors:
            try:
                items[i] = self.sensors[i]["schedule"]
            except KeyError:
                pass # Skip devices with no schedule rules

        # Iterate all devices in config
        for i in items:
            # Get list of rule trigger times, sort chronologically
            schedule = list(items[i])
            schedule.sort()

            # Get epoch time in current timezone
            epoch = time.mktime(time.localtime())

            for rule in range(0, len(schedule)):
                if rule is not len(schedule) - 1: # If current rule isn't the last rule, then end = next rule
                    end = schedule[rule+1]
                else: # If current rule IS last rule, then end = 3am (when rules are refreshed)
                    now = time.localtime(epoch)
                    if now[3] < 3:
                        end = time.mktime((now[0], now[1], now[2], 3, 0, 0, now[6], now[7]))
                    else:
                        weekday = now[6] + 1
                        if weekday == 7: weekday = 0
                        end = time.mktime((now[0], now[1], now[2]+1, 3, 0, 0, weekday, now[7]+1))

                # Check if actual epoch time is between current rule and next rule
                if schedule[rule] <= epoch < end:

                    if i.name.startswith("device"):
                        i.current_rule = self.devices[i]["schedule"][schedule[rule]]
                        i.scheduled_rule = self.devices[i]["schedule"][schedule[rule]]
                    elif i.name.startswith("sensor"):
                        i.current_rule = self.sensors[i]["schedule"][schedule[rule]]
                        i.scheduled_rule = self.sensors[i]["schedule"][schedule[rule]]

                    # Find the next rule (out of all devices)
                    # On first iteration, set next rule for current device
                    if next_rule == None:
                        next_rule = end
                    # After first, overwrite current next_rule if the next rule for current device is sooner
                    else:
                        if end < next_rule:
                            next_rule = end

                    # Stop inner loop once match found, move to next device in main loop
                    break

                #else:
                    # TODO - Test whether this functionality is worth restoring (was advantageous when this funct ran every time ligths turned on, not sure if it is now)
                    # If rule has already expired, add 24 hours (move to tomorrow same time) and delete original
                    # This fixes rules between midnight - 3am (all rules are set for current day, so these are already in the past)
                    # Originally tried this in convert_rules(), but that causes *all* rules to be in future, so no match is found here
                    #config[device]["schedule"][schedule[rule] + 86400] = config[device]["schedule"][schedule[rule]]
                    #del config[device]["schedule"][schedule[rule]]

            else:
                log.info("rule_parser: No match found for " + str(i.name))
                print("no match found\n")

        # Do not set callback timer if there are no future rules
        if not next_rule == None:
            # Set a callback timer for the next rule
            miliseconds = (next_rule - epoch) * 1000
            next_rule_timer.init(period=miliseconds, mode=Timer.ONE_SHOT, callback=self.rule_parser)
            print(f"rule_parser callback timer set for {next_rule}")
            log.debug(f"rule_parser callback timer set for {next_rule}")

        # If lights are currently on, set bool to False (forces main loop to turn lights on, new brightness takes effect)
        for i in self.sensors:
            if "MotionSensor" in str(type(i)) and i.state == True:
                i.state = False



    def find(self, target):
        if target.startswith("device"):
            for i in self.devices:
                if i.name == target:
                    return i

        elif target.startswith("sensor"):
            for i in self.sensors:
                if i.name == target:
                    return i

        else:
            return False



# Called by timer every day at 3 am, regenerate timestamps for next day (epoch time)
def reload_schedule_rules(timer):
    print("3:00 am callback, reloading schedule rules...")
    log.info("3:00 am callback, reloading schedule rules...")
    # Temporary fix: Unable to reload after 2-3 days due to mem fragmentation (no continuous free block long enough for API response)
    # Since this will take a lot of testing to figure out, just reboot until then. TODO - fix memory issue
    reboot()



def reboot(arg="unused"):
    print("Reboot function called, rebooting...")
    log.info("Reboot function called, rebooting...\n")
    import machine
    machine.reset()



# Instantiate config object
with open('config.json', 'r') as file:
    config = Config(json.load(file))
