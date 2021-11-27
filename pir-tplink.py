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



# PIR data pin connected to D15
pir = Pin(15, Pin.IN, Pin.PULL_DOWN)

# Hardware timer used to keep lights on for 5 min
timer = Timer(0)
# Timer re-runs startup every day at 3:00 am (reload schedule rules, sunrise/sunset times, etc)
rule_timer = Timer(1)

# Stops the loop from running when True, hware timer resets after 5 min
hold = False
# Set to True by motion sensor interrupt
motion = False
# Remember state of lights to prevent spamming api calls
lights = None

# Turn onboard LED on, indicates setup in progress
led = Pin(2, Pin.OUT, value=1)

# Load config file from disk
with open('config.json', 'r') as file:
    config = json.load(file)

# Connect to wifi
# TODO retry until successful
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(config["wifi"]["ssid"], config["wifi"]["password"])
webrepl.start()

# Get filesize/modification time (to detect upload in future)
old = os.stat("boot.py")



# Takes string as argument, writes to log file with YYYY/MM/DD HH:MM:SS timestamp
def log(message):
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



# Parameter isn't actually used, just has to accept one so it can be called by timer (passes itself as arg)
def startup(arg="unused"):
    print("\nRunning startup routine...\n")
    log("Running startup routine...")

    # Turn onboard LED on, indicates setup in progress
    led = Pin(2, Pin.OUT, value=1)

    # Get current time from internet, retry if request times out
    while True:
        try:
            time.sleep(2) # Without delay it always times out a couple times
            ntptime.settime()
        except OSError: # Timeout error
            # TODO - reboot after certain number of failed attempts
            print("\nTimed out getting ntp time, retrying...\n")
            continue # Restart loop to try again
        else: # Runs when no exception encountered
            break # End loop once time set successfully

    # Get offset for current timezone
    # TODO Got traceback on this line, OSError: -202 - add try/except
    response = urequests.get("http://api.timezonedb.com/v2.1/get-time-zone?key=N49YL8DI5IDS&format=json&by=zone&zone=America/Los_Angeles")
    global offset
    offset = response.json()["gmtOffset"]

    # Get sunrise/sunset time from API, returns class object
    # TODO find way to retry until successful on this and all API calls
    response = urequests.get("https://api.sunrise-sunset.org/json?lat=45.524722&lng=-122.6771891")
    # Parse out sunrise/sunset, convert to 24h format
    global sunrise
    global sunset
    sunrise = convertTime(response.json()['results']['sunrise'])
    sunset = convertTime(response.json()['results']['sunset'])

    log("Finished API calls...")

    # Convert to correct timezone
    sunrise = str(int(sunrise.split(":")[0]) + int(offset/3600)) + ":" + sunrise.split(":")[1]
    sunset = str(int(sunset.split(":")[0]) + int(offset/3600)) + ":" + sunset.split(":")[1]

    # Correct sunrise hour if it is less than 0 or greater than 23
    if int(sunrise.split(":")[0]) < 0:
        sunrise = str(int(sunrise.split(":")[0]) + 24) + ":" + sunrise.split(":")[1]
    elif int(sunrise.split(":")[0]) > 23:
        sunrise = str(int(sunrise.split(":")[0]) - 24) + ":" + sunrise.split(":")[1]

    # Correct sunset hour if it is less than 0 or greater than 23
    if int(sunset.split(":")[0]) < 0:
        sunset = str(int(sunset.split(":")[0]) + 24) + ":" + sunset.split(":")[1]
    elif int(sunset.split(":")[0]) > 23:
        sunset = str(int(sunset.split(":")[0]) - 24) + ":" + sunset.split(":")[1]

    # Load config file from disk
    global config
    with open('config.json', 'r') as file:
        config = json.load(file)

    # Convert schedule rule timestamps from HH:MM to unix epoch time
    for device in config:
        if not device.startswith("device") and not device.startswith("delay"): continue
        convert_rules(device)

    log("Finished converting schedule rules...")

    # Get epoch time of next 3:00 am (re-run timestamp to epoch conversion)
    epoch = time.mktime(time.localtime()) + offset
    now = time.localtime(epoch)
    if now[3] < 3:
        next_reset = time.mktime((now[0], now[1], now[2], 3, 0, 0, now[6], now[7]))
    else:
        next_reset = time.mktime((now[0], now[1], now[2]+1, 3, 0, 0, now[6], now[7])) # In testing, only needed to increment day - other parameters roll over correctly

    # Set interrupt to re-run setup at 3:00 am (epoch times only work once, need to refresh daily)
    next_reset = (next_reset - epoch) * 1000
    rule_timer.init(period=next_reset, mode=Timer.ONE_SHOT, callback=startup)

    # Turn off LED to confirm setup completed successfully
    led.value(0)

    log("Startup complete")



# Convert times to 24h format, also truncate seconds
def convertTime(t):
    if t[-2:] == "AM":
        if t[:2] == "12":
            time = str("00" + t[2:5]) ## Change 12:xx to 00:xx
        else:
            time = t[:-6] ## No changes just truncate seconds + AM
    elif t[-2:] == "PM":
        if t[:2] == "12":
            time = t[:-6] ## No changes just truncate seconds + AM
        else:
            # API hour does not have leading 0, so first 2 char may contain : (throws error when cast to int). This approach works with or without leading 0.
            try:
                time = str(int(t[:2]) + 12) + t[2:5] # Works if hour is double digit
            except ValueError:
                time = str(int(t[:1]) + 12) + t[1:4] # Works if hour is single-digit
    else:
        print("Fatal error: time format incorrect")
        log("convertTime: Fatal error: time format incorrect")
    return time



# Convert literal timestamps in rules into actual unix timestamps when rule will run next
# Needs to be called every 24 hours as rules will only work 1 time after being converted
def convert_rules(device):
    # Check for sunrise rule, replace "sunrise" with actual sunrise time
    if "sunrise" in config[device]["schedule"]:
        config[device]["schedule"][sunrise] = config[device]["schedule"]["sunrise"]
        del config[device]["schedule"]["sunrise"]
    # Same for sunset
    if "sunset" in config[device]["schedule"]:
        config[device]["schedule"][sunset] = config[device]["schedule"]["sunset"]
        del config[device]["schedule"]["sunset"]

    # Get rule start times
    schedule = list(config[device]["schedule"])
    schedule.sort()

    # Get epoch time in current timezone
    global offset
    epoch = time.mktime(time.localtime()) + offset
    # Get time tuple in current timezone
    now = time.localtime(epoch)

    for rule in schedule:
        # Returns epoch time of rule, uses all current parameters but substitutes hour + min from schedule and 0 for seconds
        trigger_time = time.mktime((now[0], now[1], now[2], int(rule.split(":")[0]), int(rule.split(":")[1]), 0, now[6], now[7]))

        # In ORIGINAL config dict, replace the rule timestamp with epoch time of the next run
        config[device]["schedule"][trigger_time] = config[device]["schedule"][rule]

        # Also add a rule at the same time yesterday and tomorrow - temporary workaround for bug TODO - review this, see if there is a better approach
        # Bug causes no valid rules if rebooted between last and first rule - fix will be similar to this but more efficient
        config[device]["schedule"][trigger_time-86400] = config[device]["schedule"][rule]
        config[device]["schedule"][trigger_time+86400] = config[device]["schedule"][rule]

        # Delete the original rule
        del config[device]["schedule"][rule]



# Encrypt messages to tp-link smarthome devices
def encrypt(string):
    key = 171
    result = pack(">I", len(string))
    for i in string:
        a = key ^ ord(i)
        key = a
        result += bytes([a])
    return result



# Dencrypt messages from tp-link smarthome devices
def decrypt(string):
    key = 171
    result = ""
    for i in string:
        a = key ^ i
        key = i
        result += chr(a)
    return result



# Send set_brightness command to tp-link dimmers/smartbulbs
# dev is needed because dimmer and bulb use different syntax
# state is only used by bulb, sets on/off state
# dimmer doesn't need to be turned off, just set brightness to 1 (no light below like 15 with these bulbs)
def send(ip, bright, dev, state=1):
    log("Starting send function, IP=" + str(ip) + ", Brightness=" + str(bright) + ", state=" + str(state))
    if dev == "dimmer":
        cmd = '{"smartlife.iot.dimmer":{"set_brightness":{"brightness":' + str(bright) + '}}}'
    else:
        cmd = '{"smartlife.iot.smartbulb.lightingservice":{"transition_light_state":{"ignore_default":1,"on_off":' + str(state) + ',"transition_period":0,"brightness":' + str(bright) + '}}}'

    #Send command and receive reply
    try:
        sock_tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock_tcp.settimeout(10)
        log("Created socket")
        sock_tcp.connect((ip, 9999))
        sock_tcp.settimeout(None)
        log("Connected to device")

        # Dimmer has seperate brightness and on/off commands, bulb combines into 1 command
        if dev == "dimmer":
            sock_tcp.send(encrypt('{"system":{"set_relay_state":{"state":' + str(state) + '}}}')) # Set on/off state before brightness
            log("Dimmer: Sent on/off command")
            data = sock_tcp.recv(2048) # Dimmer wont listen for next command until it's reply is received
            log("Dimmer: Received on/off reply")

        # Set brightness
        sock_tcp.send(encrypt(cmd))
        log("Sent brightness command")
        data = sock_tcp.recv(2048)
        log("Received brightness reply")
        sock_tcp.close()
        log("Closed socket")

        decrypted = decrypt(data[4:]) # Remove in final version (or put in debug conditional)

        print("Sent:     ", cmd)
        print("Received: ", decrypted)

        if state: # Lights were turned ON
            global hold
            hold = True # Keep on until reset timer expires
            global lights
            lights = True # Prevent main loop from turning on repeatedly
            log("hold + lights bools set to True")
        else: # Lights were turned OFF
            global lights
            lights = False # Prevent main loop from turning off repeatedly
            log("lights bool set to False")

    except: # Failed
        print(f"Could not connect to host {ip}")
        log("Could not connect to host " + str(ip))
        global motion
        motion = False # Allow main loop to try again immediately



def send_relay(dev, state):
    log("Starting send_relay function, IP=" + str(dev) + ", state=" + str(state))
    s = socket.socket()
    log("Created socket")
    s.connect((dev, 4200))
    log("Connected to device")
    s.send(state.encode())
    log("Sent command")
    s.close()
    log("Closed socket")
    # TODO - handle timed-out connection, currently whole thing crashes if target is unavailable
    # TODO - receive response (msg OK/Invalid), log errors



# Receive sub-dictionairy containing schedule rules, compare each against current time, return correct rule
def rule_parser(device):
    global config

    # Get list of rule trigger times, sort chronologically
    schedule = list(config[device]["schedule"])
    schedule.sort()

    # Get epoch time in current timezone
    global offset
    epoch = time.mktime(time.localtime()) + offset

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
            return schedule[rule]
            break
        else:
            # If rule has already expired, add 24 hours (move to tomorrow same time) and delete original
            # This fixes rules between midnight - 3am (all rules are set for current day, so these are already in the past)
            # Originally tried this in convert_rules(), but that causes *all* rules to be in future, so no match is found here
            config[device]["schedule"][schedule[rule] + 86400] = config[device]["schedule"][schedule[rule]]
            del config[device]["schedule"][schedule[rule]]

    else:
        log("rule_parser: No match found for " + str(device))
        print("no match found")
        print()



def resetTimer(timer):
    # Hold is set to True after lights fade on, prevents main loop from running
    # This keeps lights on until this function is called by 5 min timer
    log("resetTimer interrupt called")
    global hold
    hold = False

    # Reset motion so lights fade off next time loop runs
    global motion
    motion = False
    log("resetTimer interrupt finished")



# Interrupt routine, called when motion sensor triggered
def motion_detected(pin):
    log("motion_detected interrupt called")
    global motion
    motion = True

    # Get correct delay period based on current time
    delay = config["delay"]["schedule"][rule_parser("delay")]
    # Convert to ms
    delay = int(delay) * 60000

    # Start timer (restarts every time motion detected), calls function that resumes main loop when it times out
    timer.init(period=delay, mode=Timer.ONE_SHOT, callback=resetTimer)
    log("motion_detected interrupt finished")



startup()

# Create interrupt, call handler function when motion detected
pir.irq(trigger=Pin.IRQ_RISING, handler=motion_detected)

motion = False

log("Starting main loop...")
while True:
    if not hold: # Set to True when lights turn on, reset by timer interrupt. Prevents turning off prematurely.

        if motion:
            log("Main loop: Motion detected")
            if lights is not True: # Only turn on if currently off
                print("motion detected")
                log("Main loop: Parsing schedule rules...")
                # For each device, get correct brightness from schedule rules, set brightness
                for device in config:
                    # Dictionairy contains other entries, skip if name isn't "device<no>"
                    if not device.startswith("device"): continue
                    log("Main loop: Calling rule_parser for " + str(device))
                    # Call function that iterates rules, returns the correct rule for the current time
                    rule = rule_parser(device)
                    log("Main loop: Finished getting rule")
                    if config[device]["type"] == "relay":
                        send_relay(config[device]["ip"], config[device]["schedule"][rule])
                    else:
                        # Send parameters for the current device + rule to send function
                        send(config[device]["ip"], config[device]["schedule"][rule], config[device]["type"])
                    log("Main loop: Finished turning on" + str(device))

        else:
            if lights is not False: # Only turn off if currently on
                log("Main loop: Turning lights off...")
                for device in config:
                    if not device.startswith("device"): continue # If entry is not a device, skip
                    log("Main loop: Turning off " + str(device))
                    if config[device]["type"] == "relay":
                        send_relay(config[device]["ip"], "off")
                    else:
                        send(config[device]["ip"], config[device]["min"], config[device]["type"], 0) # Turn off
                    log("Main loop: Finished turning off " + str(device))

        time.sleep_ms(20) # TODO - is this necessary?

    else:
        # While holding (motion sensor not being checked), check if file changed on disk
        if not os.stat("boot.py") == old:
            # If file changed (new code received from webrepl), reboot
            import machine
            print("\nReceived new code from webrepl, rebooting...\n")
            log("Received new code from webrepl, rebooting...")
            time.sleep(1) # Prevents webrepl_cli.py from hanging after upload (esp reboots too fast)
            machine.reset()
        else:
            time.sleep(1) # Allow receiving upload

# TODO - turn on LED and write log lines here, will run if uncaught exception breaks the loop

# TODO - wrap whole script in try/except (in boot.py, run this code with execfile inside try)
