# This file is executed on every boot (including wake-boot from deepsleep)
#import esp
#esp.osdebug(None)

import webrepl
import network
import time
import ntptime
from machine import Pin, PWM, Timer
import urequests
import json

# PWM pin for LED strip
pwm = PWM(Pin(4), duty=0)
pwm.duty(0) # Firmware bug workaround (in above line, duty=0 is ignored ~10% of the time)

# PIR data pin connected to D15
pir = Pin(15, Pin.IN)

# Interrupt button reconnects to wifi (for debug/uploading new code)
button = Pin(16, Pin.IN)

# Used to set pwm duty cycle
bright = 0

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
    try:
        wlan = network.WLAN(network.STA_IF)
        wlan.active(True)
        wlan.connect(config["wifi"]["ssid"], config["wifi"]["password"])
    except OSError: # Rare error, cannot be recovered, reboot
        import machine
        machine.reset()

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
    wlan.disconnect()
    wlan.active(False)

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



def fade(state):
    global bright
    if state == "on":
        while bright < 32:
            bright = bright + 1
            pwm.duty(bright)
            time.sleep_ms(32)

        # Prevent loop from running (keeps lights on)
        global hold
        hold = True

    elif state == "off":
        while bright > 0:
            bright = bright - 1
            pwm.duty(bright)
            time.sleep_ms(32)



# Create interrupt, call handler function when motion detected
pir.irq(trigger=Pin.IRQ_RISING, handler=motion_detected)
# Call function when button pressed, used for uploading new code
button.irq(trigger=Pin.IRQ_RISING, handler=buttonInterrupt)



startup()

while True:
    # wifi = False unless user presses interrupt button
    if not wifi:
        if not hold:

            if motion:
                now = time.localtime() # Create tuple, param 3 = hour
                # Change timezone function in library is broken so stuck on GMT time
                # In Spring/Summer/Fall sunset is 12-4 am GMT, so the else conditional is used
                # In Winter sunset rolls over to 10-11 pm GMT, requiring 2 conditionals
                if sunset > sunrise:
                    if 0 <= now[3] <= sunrise or sunset <= now[3] <= 23: # If after sunset + before sunrise
                        fade("on")
                    else:
                        motion = False
                else:
                    if sunset <= now[3] <= sunrise: # If after sunset + before sunrise
                        fade("on")
                    else:
                        motion = False

            else:
                fade("off")

            time.sleep_ms(20)

    # If user pressed button, reconnect to wifi, start webrepl, break loop
    else:
        print("Entering maintenance mode")
        global wlan
        wlan.active(True)
        wlan.connect(config["wifi"]["ssid"], config["wifi"]["password"])
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
