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



# PIR data pin connected to D15
pir = Pin(15, Pin.IN, Pin.PULL_DOWN)

# Interrupt button reconnects to wifi (for debug/uploading new code)
button = Pin(16, Pin.IN)

# Hardware timer used to keep lights on for 5 min
timer = Timer(0)
# Hardware timer used to call API for sunrise/sunset time
api_timer = Timer(1)
# Timer reloads schedule rules every day at 3:00 am
rule_timer = Timer(2)

# Stops the loop from running when True, hware timer resets after 5 min
hold = False
# Set to True by motion sensor interrupt
motion = False
# Set to True by interrupt button
wifi = False
# Remember state of lights to prevent spamming api calls
lights = None

# Load config file
with open('config.json', 'r') as file:
    config = json.load(file)

# Parameter isn't actually used, just has to accept one so it can be called by timer (passes itself as arg)
def startup(arg="unused"):
    # Turn onboard LED on, indicates setup in progress
    led = Pin(2, Pin.OUT, value=1)

    # Connect to wifi
    global wlan
    global config
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(config["wifi"]["ssid"], config["wifi"]["password"])

    # Get current time from internet, retry if request times out
    while True:
        try:
            time.sleep(2) # Without delay it always times out a couple times
            ntptime.settime()
        except OSError: # Timeout error
            print("\nTimed out getting ntp time, retrying...\n")
            continue # Restart loop to try again
        else: # Runs when no exception encountered
            break # End loop once time set successfully

    # Get sunrise/sunset time from API, returns class object
    response = urequests.get("https://api.sunrise-sunset.org/json?lat=45.524722&lng=-122.6771891")
    # Parse out sunrise/sunset, convert to 24h format
    global sunrise
    global sunset
    sunrise = convertTime(response.json()['results']['sunrise'])
    sunset = convertTime(response.json()['results']['sunset'])

    # Get offset for current timezone
    response = urequests.get("http://api.timezonedb.com/v2.1/get-time-zone?key=N49YL8DI5IDS&format=json&by=zone&zone=America/Los_Angeles")
    global offset
    offset = response.json()["gmtOffset"]

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

    # Convert timestamps for each schedule rule into the literal epoch time when it runs
    for device in config:
        # Dictionairy contains other entries, skip if name isn't "device<no>"
        if not device.startswith("device") and not device.startswith("delay"): continue
        convert_rules(device)

    # Get epoch time of next 3:00 am (re-run timestamp to epoch conversion)
    epoch = time.mktime(time.localtime()) + offset
    now = time.localtime(epoch)
    if now[3] < 3:
        next_reset = time.mktime((now[0], now[1], now[2], 3, 0, 0, now[6], 311))
    else:
        weekday = now[6] + 1
        if weekday == 7: weekday = 0
        next_reset = time.mktime((now[0], now[1], now[2]+1, 3, 0, 0, weekday, 311))

    # Set interrupt to run at 3:00 am
    next_reset = (next_reset - epoch) * 1000
    rule_timer.init(period=next_reset, mode=Timer.ONE_SHOT, callback=reset_rules_interrupt)

    # Disconnect from wifi to reduce power usage
    #wlan.disconnect()
    #wlan.active(False)
    webrepl.start()

    # Re-run startup every 5 days to get up-to-date sunrise/sunset times
    api_timer.init(period=432000000, mode=Timer.ONE_SHOT, callback=startup)

    # Turn off LED to confirm setup completed successfully
    led.value(0)



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
        del config[device]["schedule"][rule]



def reset_rules_interrupt(timer):
    print("Interrupt: Refreshing schedule rules...")

    global config

    # Reload rules from disk (overwriting the old epoch timestamps from yesterday)
    with open('config.json', 'r') as file:
        config = json.load(file)

    # Generate timestamps for the next day
    for device in config:
        if not device.startswith("device") and not device.startswith("delay"): continue
        convert_rules(device)

    # Get epoch time in current timezone
    global offset
    epoch = time.mktime(time.localtime()) + offset
    # Get time tuple in current timezone
    now = time.localtime(epoch)

    # Get epoch time of next 3:00 am
    if now[3] < 3:
        next_reset = time.mktime((now[0], now[1], now[2], 3, 0, 0, now[6], now[7]))
    else:
        weekday = now[6] + 1
        if weekday == 7: weekday = 0
        next_reset = time.mktime((now[0], now[1], now[2]+1, 3, 0, 0, weekday, now[7]+1))

    # Set interrupt to run at 3:00 am
    next_reset = (next_reset - epoch) * 1000
    rule_timer.init(period=next_reset, mode=Timer.ONE_SHOT, callback=reset_rules_interrupt)



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
    if dev == "dimmer":
        cmd = '{"smartlife.iot.dimmer":{"set_brightness":{"brightness":' + str(bright) + '}}}'
    else:
        cmd = '{"smartlife.iot.smartbulb.lightingservice":{"transition_light_state":{"ignore_default":1,"on_off":' + str(state) + ',"transition_period":0,"brightness":' + str(bright) + '}}}'

    #Send command and receive reply
    try:
        sock_tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock_tcp.settimeout(10)
        sock_tcp.connect((ip, 9999))
        sock_tcp.settimeout(None)

        # Dimmer has seperate brightness and on/off commands, bulb combines into 1 command
        if dev == "dimmer":
            sock_tcp.send(encrypt('{"system":{"set_relay_state":{"state":' + str(state) + '}}}')) # Set on/off state before brightness
            data = sock_tcp.recv(2048) # Dimmer wont listen for next command until it's reply is received

        # Set brightness
        sock_tcp.send(encrypt(cmd))
        data = sock_tcp.recv(2048)
        sock_tcp.close()

        decrypted = decrypt(data[4:]) # Remove in final version (or put in debug conditional)

        print("Sent:     ", cmd)
        print("Received: ", decrypted)

        if state: # Lights were turned ON
            global hold
            hold = True # Keep on until reset timer expires
            global lights
            lights = True # Prevent main loop from turning on repeatedly
        else: # Lights were turned OFF
            global lights
            lights = False # Prevent main loop from turning off repeatedly

    except: # Failed
        print(f"Could not connect to host {ip}")
        global motion
        motion = False # Allow main loop to try again immediately



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
            # If rule has already expired, delete it so it doesn't have to be checked again
            # Will be re-added tomorrow when rules refresh
            del config[device]["schedule"][schedule[rule]]

    else:
        print("no match found")
        print()



# Breaks main loop, reconnects to wifi, starts webrepl (for debug/uploading new code)
def buttonInterrupt(pin):
    global wifi
    wifi = True



def resetTimer(timer):
    # Hold is set to True after lights fade on, prevents main loop from running
    # This keeps lights on until this function is called by 5 min timer
    global hold
    hold = False

    # Reset motion so lights fade off next time loop runs
    global motion
    motion = False



# Interrupt routine, called when motion sensor triggered
def motion_detected(pin):
    global motion
    motion = True

    # Get correct delay period based on current time
    delay = config["delay"]["schedule"][rule_parser("delay")]
    # Convert to ms
    delay = int(delay) * 60000

    # Start timer (restarts every time motion detected), calls function that resumes main loop when it times out
    timer.init(period=delay, mode=Timer.ONE_SHOT, callback=resetTimer)



startup()

# Create interrupt, call handler function when motion detected
pir.irq(trigger=Pin.IRQ_RISING, handler=motion_detected)
# Call function when button pressed, used for uploading new code
button.irq(trigger=Pin.IRQ_RISING, handler=buttonInterrupt)

motion = False

while True:
    # wifi = False unless user presses interrupt button
    if not wifi:
        if not hold: # Set to True when lights turn on, reset by timer interrupt. Prevents turning off prematurely.

            if motion:
                if lights is not True: # Only turn on if currently off
                    print("motion detected")

                    # For each device, get correct brightness from schedule rules, set brightness
                    for device in config:
                        # Dictionairy contains other entries, skip if name isn't "device<no>"
                        if not device.startswith("device"): continue

                        # Call function that iterates rules, returns the correct rule for the current time
                        rule = rule_parser(device)

                        # Send parameters for the current device + rule to send function
                        send(config[device]["ip"], config[device]["schedule"][rule], config[device]["type"])

            else:
                if lights is not False: # Only turn off if currently on

                    for device in config:
                        if not device.startswith("device"): continue # If entry is not a device, skip
                        send(config[device]["ip"], config[device]["min"], config[device]["type"], 0) # Turn off

            time.sleep_ms(20)

    # If user pressed button, reconnect to wifi, start webrepl, break loop
    else:
        print("\nEntering maintenance mode\n")
        print("Device identifier: {0}".format(config["metadata"]["id"]))
        print("Device location: {0}".format(config["metadata"]["location"]))
        global wlan
        wlan.active(True)
        wlan.connect(config["wifi"]["ssid"], config["wifi"]["password"])
        print("Device IP: {0}\n".format(wlan.ifconfig()[0]))
        webrepl.start()
        # LED indicates maintenance mode, stays on until unit reset
        led = Pin(2, Pin.OUT, value=1)
        # Break loop to allow webrepl connections
        break



# Automatically reboot when file on disk has changed (webrepl upload complete)
# Only runs if maintenance mode button was pressed
import machine
import os
old = os.stat("boot.py")
while True:
    new = os.stat("boot.py")
    if new == old:
        time.sleep(1)
    else:
        print("Upload complete, rebooting...")
        time.sleep(1) # Prevents webrepl_cli.py from hanging after upload (esp reboots too fast)
        machine.reset()
