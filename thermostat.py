# Required dependency: Chris Balmer's si7021 library:
# https://github.com/chrisbalmer/micropython-si7021
#
# Use webrepl to upload si7021.py to /lib

import webrepl
import network
import time
from machine import Pin, Timer, RTC, SoftI2C
import urequests
import socket
from struct import pack
import json
import os
import _thread
from random import randrange

try:
    import si7021
except:
    print("FATAL ERROR: si7021 library not installed")
    print("https://github.com/chrisbalmer/micropython-si7021")
    led = Pin(2, Pin.OUT, value=1)
    while True:
        led.value(1)
        time.sleep(0.1)
        led.value(0)
        time.sleep(0.1)


print("--------Booted--------")

# PIR data pin connected to D15
pir = Pin(15, Pin.IN, Pin.PULL_DOWN)

# Hardware timer used to keep lights on for 5 min
timer = Timer(0)
# Timer re-runs startup every day at 3:00 am (reload schedule rules, sunrise/sunset times, etc)
config_timer = Timer(1)
# Used to reboot if startup hangs for longer than 1 minute
reboot_timer = Timer(2)
# Used when it is time to switch to the next schedule rule
next_rule_timer = Timer(3)

# Set to True by motion sensor interrupt
motion = False
# Remember state of lights to prevent spamming api calls
lights = None
# Timer sets this to True at 3:00 am, causes main loop to reload config
reload_config = False

# Turn onboard LED on, indicates setup in progress
led = Pin(2, Pin.OUT, value=1)



class Thermostat():
    def __init__(self, name, target, setting):
        # Setup I2C interface
        self.i2c = SoftI2C(Pin(22), Pin(21))
        self.temp_sensor = si7021.Si7021(self.i2c)

        self.name = name

        self.setting = int(setting)

        for device in config.devices:
            if device.name == target:
                self.target = device

        _thread.start_new_thread(self.loop, ())



    def fahrenheit(self):
        return si7021.convert_celcius_to_fahrenheit(self.temp_sensor.temperature)



    def loop(self):
        while True:
            current = self.fahrenheit()
            if current < (self.setting - 1):
                print(f"Current temp ({current}) less than setting ({self.setting})")
                self.target.send(1)
            elif current > (self.setting + 1):
                print(f"Current temp ({current}) greater than setting ({self.setting})")
                self.target.send(0)

            time.sleep(15)



class Config():
    def __init__(self, conf):
        print("\nInstantiating config object...\n")
        log("Instantiating config object...")

        # Load wifi credentials tuple
        self.credentials = (conf["wifi"]["ssid"], conf["wifi"]["password"])

        # Load metadata parameters - (unused so far)
        self.identifier = conf["metadata"]["id"]
        self.location = conf["metadata"]["location"]
        self.floor = conf["metadata"]["floor"]

        # Call function to connect to wifi + hit APIs
        self.api_calls()

        # Create sub-dict containing delay schedule rules (how long lights stay on after motion)
        #self.delay = {}
        #self.delay["schedule"] = self.convert_rules(conf["delay"]["schedule"])

        # Create empty dictionairy, will contain sub-dict for each device
        self.devices = {}

        # Iterate json
        for device in conf:
            if not device.startswith("device"): continue

            # Instantiate each device as appropriate class
            if conf[device]["type"] == "dimmer" or conf[device]["type"] == "bulb":
                instance = Tplink( device, conf[device]["ip"], conf[device]["type"], None )
            elif conf[device]["type"] == "relay" or conf[device]["type"] == "desktop":
                instance = Relay( device, conf[device]["ip"], None )

            # Add to self.devices dict with class object as key + json sub-dict as value
            self.devices[instance]  = conf[device]
            # Overwrite schedule section with unix timestamp rules
            #self.devices[instance]["schedule"] = self.convert_rules(conf[device]["schedule"])

        for sensor in conf:
            if not sensor.startswith("sensor"): continue

            if conf[sensor]["type"] == "si7021":
                # Temporarily load whole contents, will be replaced by Thermostat init method later
                self.thermostat = conf[sensor]

        #self.rule_parser()

        log("Finished instantiating config")



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
                log("Failed setting system time, retrying...")
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
                log("Failed getting sunrise/sunset time, retrying...")
                failed_attempts += 1
                if failed_attempts > 5: reboot()
                time.sleep_ms(1500) # If failed, wait 1.5 seconds before retrying
                gc.collect() # Free up memory before retrying
                pass # Allow loop to continue

        log("Finished API calls...")

        # Stop timer once API calls finish
        reboot_timer.deinit()

        # Turn off LED to confirm setup completed successfully
        led.value(0)



    # Convert times to 24h format, also truncate seconds
    def convert_time(self, t):
        if t[-2:] == "AM":
            if t[:2] == "12":
                time = str("00" + t[2:5]) ## Change 12:xx to 00:xx
            else:
                time = t[:-6] # No changes just truncate seconds + AM
        elif t[-2:] == "PM":
            if t[:2] == "12":
                time = t[:-6] # No changes just truncate seconds + AM
            else:
                # API hour does not have leading 0, so first 2 char may contain : (throws error when cast to int). This approach works with or without leading 0.
                try:
                    time = str(int(t[:2]) + 12) + t[2:5] # Works if hour is double digit
                except ValueError:
                    time = str(int(t[:1]) + 12) + t[1:4] # Works if hour is single-digit
        else:
            print("Fatal error: time format incorrect")
            log("convert_time: Fatal error: time format incorrect")
        return time



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
        items["delay"] = self.delay["schedule"]

        for i in self.devices:
            items[i] = self.devices[i]["schedule"]


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

                    if i == "delay":
                        self.delay["current"] = self.delay["schedule"][schedule[rule]]
                    else:
                        for device in self.devices:
                            if i == device:
                                if "Tplink" in str(device):
                                    device.brightness = self.devices[device]["schedule"][schedule[rule]]
                                else:
                                    device.enabled = self.devices[device]["schedule"][schedule[rule]]

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
                    # If rule has already expired, add 24 hours (move to tomorrow same time) and delete original
                    # This fixes rules between midnight - 3am (all rules are set for current day, so these are already in the past)
                    # Originally tried this in convert_rules(), but that causes *all* rules to be in future, so no match is found here
                    #config[device]["schedule"][schedule[rule] + 86400] = config[device]["schedule"][schedule[rule]]
                    #del config[device]["schedule"][schedule[rule]]

            else:
                log("rule_parser: No match found for " + str(device))
                print("no match found")
                print()

        # Set a callback timer for the next rule
        miliseconds = (next_rule - epoch) * 1000
        next_rule_timer.init(period=miliseconds, mode=Timer.ONE_SHOT, callback=self.rule_parser)
        print(f"rule_parser callback timer set for {next_rule}")

        # If lights are currently on, set bool to False (forces main loop to turn lights on, new brightness takes effect)
        global lights
        if lights:
            lights = False



# Used for ESP8266 Relays + Desktops (running desktop-integration.py)
class Relay():
    def __init__(self, name, ip, enabled):
        self.name = name
        self.ip = ip
        self.enabled = enabled
        log("Created Relay class instance named " + str(self.name) + ": ip = " + str(self.ip))



    def send(self, state=1):
        log("Relay.send method called, IP = " + str(self.ip) + ", state = " + str(state))
        if self.enabled == "off" and state == 1:
            pass
        else:
            s = socket.socket()
            print(f"Running send_relay, ip={self.ip}")
            s.connect((self.ip, 4200))
            if state:
                print(f"Turned {self.name} ON")
                s.send("on".encode())
            else:
                print(f"Turned {self.name} OFF")
                s.send("off".encode())
            s.close()
            log("Relay.send finished")
            # TODO - handle timed-out connection, currently whole thing crashes if target is unavailable
            # TODO - receive response (msg OK/Invalid), log errors



# Takes string as argument, writes to log file with YYYY/MM/DD HH:MM:SS timestamp
def log(message):
    # TODO - when disk fills up, writing log causes OSError: 28 and everything hangs
    # Could wrap this in try/except and delete log if OSError
    # Probably better to just run a timer callback and check filesize every hour or something
    now = time.localtime()
    line = str(now[0]) + "/"
    for i in range(1,3):
        if len(str(now[i])) == 1:
            line = line + "0" + str(now[i]) + "/"
        else:
            line = line + str(now[i]) + "/"
    else:
        line = line[0:-1] + " " # Replace trailing "/" with " "
    for i in range(3,6):
        if len(str(now[i])) == 1:
            line = line + "0" + str(now[i]) + ":"
        else:
            line = line + str(now[i]) + ":"
    else:
        line = line + " " + message + "\n"

    with open('log.txt', 'a') as file:
        file.write(line)



# Called by timer every day at 3 am, regenerate timestamps for next day (epoch time)
def reload_schedule_rules(timer):
    print("3:00 am callback, reloading schedule rules...")
    log("3:00 am callback, reloading schedule rules...")
    #global config
    #config = Config(json.load(open('config.json', 'r')))
    global reload_config
    reload_config = True



def reboot(arg="unused"):
    print("Reboot function called, rebooting...")
    log("Reboot function called, rebooting...\n")
    import machine
    machine.reset()



def listen_for_upload():
    # Get filesize/modification time (to detect upload in future)
    old_code = os.stat("boot.py")
    old_config = os.stat("config.json")

    while True:
        # Check if file changed on disk
        if not os.stat("boot.py") == old_code:
            # If file changed (new code received from webrepl), reboot
            print("\nReceived new code from webrepl, rebooting...\n")
            log("Received new code from webrepl, rebooting...")
            time.sleep(1) # Prevents webrepl_cli.py from hanging after upload (esp reboots too fast)
            reboot()
        elif not os.stat("config.json") == old_config:
            # If file changed (new config received from webrepl), reboot
            print("\nReceived new config from webrepl, rebooting...\n")
            log("Received new config from webrepl, rebooting...")
            time.sleep(1) # Prevents webrepl_cli.py from hanging after upload (esp reboots too fast)
            reboot()
        else:
            time.sleep(1) # Only check once per second



# Don't let log exceed 500 KB - can fill disk, also cannot be pulled via webrepl without timing out
# TODO move this into listen_for_upload, rename disk_monitor or something
try:
    if os.stat('log.txt')[6] > 500000:
        print("\nLog exceeded 500 KB, clearing...\n")
        os.remove('log.txt')
        log("Deleted old log (exceeded 500 KB size limit)")
except OSError: # File does not exist
    pass



# Instantiate config object - init method replaces old startup function (convert rules, connect to wifi, API calls, etc)
config = Config(json.load(open('config.json', 'r')))

# Instantiate thermostat object
thermostat = Thermostat( "si7021", config.thermostat["target"], config.thermostat["default_setting"] )

webrepl.start()

# Start thread listening for upload so unit will auto-reboot if code is updated
_thread.start_new_thread(listen_for_upload, ())
