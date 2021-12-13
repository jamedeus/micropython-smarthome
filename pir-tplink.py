# This file is executed on every boot (including wake-boot from deepsleep)
#import esp
#esp.osdebug(None)

import webrepl
import network
import time
import ntptime
from machine import Pin, Timer
import urequests
import socket
from struct import pack
import json
import os
import _thread
from random import randrange



# PIR data pin connected to D15
pir = Pin(15, Pin.IN, Pin.PULL_DOWN)

# Hardware timer used to keep lights on for 5 min
timer = Timer(0)
# Timer re-runs startup every day at 3:00 am (reload schedule rules, sunrise/sunset times, etc)
rule_timer = Timer(1)
# Used to reboot if startup hangs for longer than 1 minute
reboot_timer = Timer(2)
# Used when it is time to switch to the next schedule rule
next_rule_timer = Timer(3)

# Set to True by motion sensor interrupt
motion = False
# Remember state of lights to prevent spamming api calls
lights = None

# Turn onboard LED on, indicates setup in progress
led = Pin(2, Pin.OUT, value=1)



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
        self.delay = {}
        self.delay["schedule"] = self.convert_rules(conf["delay"]["schedule"])

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
            self.devices[instance]["schedule"] = self.convert_rules(conf[device]["schedule"])

        self.rule_parser()

        log("Finished instantiating config")



    def api_calls(self):
        # Auto-reboot if startup doesn't complete in 1 min (prevents API calls hanging, canceled at bottom of function)
        reboot_timer.init(period=60000, mode=Timer.ONE_SHOT, callback=reboot)

        # Turn onboard LED on, indicates setup in progress
        led = Pin(2, Pin.OUT, value=1)

        # Connect to wifi
        wlan = network.WLAN(network.STA_IF)
        wlan.active(True)
        wlan.connect(self.credentials[0], self.credentials[1])

        # Wait until finished connecting before proceeding
        while not wlan.isconnected():
            continue
        else:
            print(f"Successfully connected to {self.credentials[0]}")

        # Get current time from internet, retry if request times out
        while True:
            try:
                ntptime.settime()
                break # Break loop once request succeeds
            except:
                print("\nTimed out getting ntp time, retrying...\n")
                log("Timed out getting ntp time, retrying...")
                pass # Allow loop to continue

        # Get offset for current timezone, retry until successful
        while True:
            try:
                response = urequests.get("http://api.timezonedb.com/v2.1/get-time-zone?key=N49YL8DI5IDS&format=json&by=zone&zone=America/Los_Angeles")
                self.offset = response.json()["gmtOffset"]
                break # Break loop once request succeeds
            except:
                print("Failed getting timezone, retrying...")
                log("Failed getting timezone, retrying...")
                time.sleep_ms(1500) # If failed, wait 1.5 seconds before retrying
                pass # Allow loop to continue

        # Get sunrise/sunset time, retry until successful
        while True:
            try:
                response = urequests.get("https://api.sunrise-sunset.org/json?lat=45.524722&lng=-122.6771891")
                # Parse out sunrise/sunset, convert to 24h format
                self.sunrise = self.convert_time(response.json()['results']['sunrise'])
                self.sunset = self.convert_time(response.json()['results']['sunset'])
                break # Break loop once request succeeds
            except:
                print("Failed getting sunrise/sunset time, retrying...")
                log("Failed getting sunrise/sunset time, retrying...")
                time.sleep_ms(1500) # If failed, wait 1.5 seconds before retrying
                pass # Allow loop to continue

        log("Finished API calls...")

        # Stop timer once API calls finish
        reboot_timer.deinit()

        # Turn off LED to confirm setup completed successfully
        led.value(0)

        # Convert sunrise/sunset to correct timezone
        self.sunrise = str(int(self.sunrise.split(":")[0]) + int(self.offset/3600)) + ":" + self.sunrise.split(":")[1]
        self.sunset = str(int(self.sunset.split(":")[0]) + int(self.offset/3600)) + ":" + self.sunset.split(":")[1]

        # Correct sunrise hour if less than 0 or greater than 23
        if int(self.sunrise.split(":")[0]) < 0:
            self.sunrise = str(int(self.sunrise.split(":")[0]) + 24) + ":" + self.sunrise.split(":")[1]
        elif int(self.sunrise.split(":")[0]) > 23:
            self.sunrise = str(int(self.sunrise.split(":")[0]) - 24) + ":" + self.sunrise.split(":")[1]

        # Correct sunset hour if less than 0 or greater than 23
        if int(self.sunset.split(":")[0]) < 0:
            self.sunset = str(int(self.sunset.split(":")[0]) + 24) + ":" + self.sunset.split(":")[1]
        elif int(sunset.split(":")[0]) > 23:
            self.sunset = str(int(self.sunset.split(":")[0]) - 24) + ":" + self.sunset.split(":")[1]



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
        epoch = time.mktime(time.localtime()) + self.offset
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
            epoch = time.mktime(time.localtime()) + self.offset

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



# Used for TP-Link Kasa dimmers + smart bulbs
class Tplink():
    def __init__(self, name, ip, device, brightness):
        self.name = name
        self.ip = ip
        self.device = device
        self.brightness = brightness
        log("Created Tplink class instance named " + str(self.name) + ": ip = " + str(self.ip) + ", type = " + str(self.device))



    # Encrypt messages to tp-link smarthome devices
    def encrypt(self, string):
        key = 171
        result = pack(">I", len(string))
        for i in string:
            a = key ^ ord(i)
            key = a
            result += bytes([a])
        return result



    # Decrypt messages from tp-link smarthome devices
    def decrypt(self, string):
        key = 171
        result = ""
        for i in string:
            a = key ^ i
            key = i
            result += chr(a)
        return result



    def send(self, state=1):
        log("Tplink.send method called, IP=" + str(self.ip) + ", Brightness=" + str(self.brightness) + ", state=" + str(state))
        if self.device == "dimmer":
            cmd = '{"smartlife.iot.dimmer":{"set_brightness":{"brightness":' + str(self.brightness) + '}}}'
        else:
            cmd = '{"smartlife.iot.smartbulb.lightingservice":{"transition_light_state":{"ignore_default":1,"on_off":' + str(state) + ',"transition_period":0,"brightness":' + str(self.brightness) + '}}}'

        # Send command and receive reply
        try:
            sock_tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock_tcp.settimeout(10)
            sock_tcp.connect((self.ip, 9999))
            #sock_tcp.settimeout(None)
            log("Connected")

            # Dimmer has seperate brightness and on/off commands, bulb combines into 1 command
            if self.device == "dimmer":
                sock_tcp.send(self.encrypt('{"system":{"set_relay_state":{"state":' + str(state) + '}}}')) # Set on/off state before brightness
                data = sock_tcp.recv(2048) # Dimmer wont listen for next command until it's reply is received
                log("Sent state (dimmer)")

            # Set brightness
            sock_tcp.send(self.encrypt(cmd))
            log("Sent brightness")
            data = sock_tcp.recv(2048)
            log("Received reply")
            sock_tcp.close()

            decrypted = self.decrypt(data[4:]) # Remove in final version (or put in debug conditional)

            print("Sent:     ", cmd)
            print("Received: ", decrypted)

            if state: # Lights were turned ON
                global lights
                lights = True # Prevent main loop from turning on repeatedly
            else: # Lights were turned OFF
                global lights
                lights = False # Prevent main loop from turning off repeatedly
                # TODO - schedule this to run in 5 seconds, otherwise if first device fails but second succeeds it will not try again!

        except: # Failed
            print(f"Could not connect to host {self.ip}")
            log("Could not connect to host " + str(self.ip))
            global motion
            motion = True
            global lights
            lights = False # Allow main loop to try again immediately



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
                print("Turned desktop ON")
                s.send("on".encode())
            else:
                print("Turned desktop OFF")
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
    Config(json.load(open('config.json', 'r')))



def reboot(arg="unused"):
    log("Reboot function called, rebooting...\n")
    import machine
    machine.reset()



def resetTimer(timer):
    # Hold is set to True after lights fade on, prevents main loop from running
    # This keeps lights on until this function is called by 5 min timer
    log("resetTimer interrupt called")

    # Reset motion so lights fade off next time loop runs
    global motion
    motion = False



# Interrupt routine, called when motion sensor triggered
def motion_detected(pin):
    global motion
    motion = True

    # Set reset timer
    global delay

    if not "None" in str(config.delay["current"]):
        off = int(config.delay["current"]) * 60000 # Convert to ms
        # Start timer (restarts every time motion detected), calls function that resumes main loop when it times out
        timer.init(period=off, mode=Timer.ONE_SHOT, callback=resetTimer)
    else:
        # Stop any reset timer that may be running from before delay = None
        timer.deinit()



# Receive messages when desktop turns overhead lights on/off, change bools to reflect
def desktop_integration():
    # Create socket listening on port 4200
    s = socket.socket()
    s.bind(('', 4200)) # TODO add port in config, replace hardcoded value
    s.listen(1)

    # Handle connections
    while True:
        # Accept connection, decode message
        conn, addr = s.accept()
        msg = conn.recv(8).decode()

        if msg == "on": # Unsure if this will be used - currently desktop only turns lights off (when monitors sleep)
            print("Desktop turned lights ON")
            log("Desktop turned lights ON")
            global lights
            lights = True
            global motion
            motion = True
        if msg == "off": # Allow main loop to continue when desktop turns lights off
            print("Desktop turned lights OFF")
            log("Desktop turned lights OFF")
            global lights
            lights = False
            global motion
            motion = False



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

webrepl.start()

# Create interrupt, call handler function when motion detected
pir.irq(trigger=Pin.IRQ_RISING, handler=motion_detected)

# Start thread listening for upload so unit will auto-reboot if code is updated
_thread.start_new_thread(listen_for_upload, ())

# Check if desktop integration is being used
for device in config.devices:
    if config.devices[device]["type"] == "desktop":
        # Create thread, listen for messages from desktop and keep lights boolean in sync
        _thread.start_new_thread(desktop_integration, ())
        log("Desktop integration is being used, starting thread to listen for messages")
        break # Only need 1 thread, stop loop after first match



# Get epoch time of next 3:00 am (re-run timestamp to epoch conversion)
epoch = time.mktime(time.localtime()) + config.offset
now = time.localtime(epoch)
if now[3] < 3:
    next_reset = time.mktime((now[0], now[1], now[2], 3, 0, 0, now[6], now[7]))
else:
    next_reset = time.mktime((now[0], now[1], now[2]+1, 3, 0, 0, now[6], now[7])) # In testing, only needed to increment day - other parameters roll over correctly

# Set timer to reload schedule rules at a random time between 3-4 am (prevent multiple units hitting API at same second)
next_reset = (next_reset - epoch + randrange(3600)) * 1000
rule_timer.init(period=next_reset, mode=Timer.ONE_SHOT, callback=reload_schedule_rules)



log("Starting main loop...")
while True:
    if motion:

        if lights is not True: # Only turn on if currently off
            log("Motion detected (main loop)")
            print("motion detected")

            # Call send method of each class instance, argument = turn ON
            for device in config.devices:
                device.send(1)

    else:
        if lights is not False: # Only turn off if currently on
            log("Main loop: Turning lights off...")

            # Call send method of each class instance, argument = turn OFF
            for device in config.devices:
                device.send(0)

    time.sleep_ms(20) # TODO - is this necessary?



# TODO - turn on LED and write log lines here, will run if uncaught exception breaks the loop
