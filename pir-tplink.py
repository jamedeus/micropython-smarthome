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
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect('jamnet', 'cjZY8PTa4ZQ6S83A')

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
    # Convert to dictionairy - first index is response code, second index contains all location data
    response = response.json()
    # Select the second index and load it as another dict that can be parsed further
    response = response['results']
    # Parse desired params
    global sunrise
    global sunset
    sunrise = response['sunrise']
    sunset = response['sunset']

    # Convert to 24h format
    sunrise = convertTime(sunrise)
    sunset = convertTime(sunset)

    # Truncate minutes
    sunrise = sunrise.split(":")[0]
    sunset = sunset.split(":")[0]

    # Move sunrise 1 hour later, sunset 1 hour earlier (fix issues from truncated minutes)
    sunrise = int(sunrise) + 1
    sunset = int(sunset) - 1

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
def rule_parser(entry):
    global config

    # Get hour in correct timezone
    hour = time.localtime()[3] - 7
    if hour < 0:
        hour = hour + 24

    # Get rule start times, sort by time
    schedule = list(config[entry]["schedule"])
    schedule.sort()

    for rule in range(0, len(schedule)):
        # The rules are sorted chronologically, so each rule ends when the next indexed rule begins

        startHour = int(schedule[rule][0:2]) # Cut hour, cast as int
        startMin = int(schedule[rule][3:5]) # Cut minute, cast as int

        if rule is not len(schedule) - 1: # If current rule isn't the last rule, then endHour = next rule
            endHour = int(schedule[rule+1][0:2])
            endMin = int(schedule[rule+1][3:5])
        else:
            endHour = int(schedule[0][0:2]) # If current rule IS last rule, then endHour = first rule
            endMin = int(schedule[0][3:5])

        # Check if current hour is between startHour and endHour
        if endHour > startHour:
            if startHour <= hour < endHour: # Can ignore minutes if next rule is in a different hour
                return schedule[rule] # Return correct rule to the calling function
                break # Break loop
        elif startHour == hour == endHour:
            minute = time.localtime()[4] # Get current minutes
            if startMin <= minute < endMin: # Need to check minutes when start/end hours are same
                return schedule[rule] # Return correct rule to the calling function
                break # Break loop
        else:
            if startHour <= hour <= 23 or 0 <= hour < endHour: # Can ignore minutes, but need different conditional for hours when end < start
                return schedule[rule] # Return correct rule to the calling function
                break # Break loop



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



# Create interrupt, call handler function when motion detected
pir.irq(trigger=Pin.IRQ_RISING, handler=motion_detected)
# Call function when button pressed, used for uploading new code
button.irq(trigger=Pin.IRQ_RISING, handler=buttonInterrupt)



startup()

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
        print("Entering maintenance mode")
        global wlan
        wlan.active(True)
        wlan.connect('jamnet', 'cjZY8PTa4ZQ6S83A')
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
