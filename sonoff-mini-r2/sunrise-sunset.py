import webrepl
import network
import time
import ntptime
import json
import socket
import os
from machine import Pin, Timer

relay = Pin(12, Pin.OUT)
switch = Pin(4, Pin.IN)

# Timer re-runs startup every day at 3:00 am (reload sunrise/sunset times, daylight savings, etc)
api_timer = Timer(0)

# Call interrupts to turn light on/off at sunset/sunrise
sunrise_timer = Timer(1)
sunset_timer = Timer(2)

# Get filesize/modification time (to detect upload in future)
old = os.stat("boot.py")

# Stay connected to wifi + enable hot-reload for testing
# This should be set to True when first installed in wall
# Allows fixing bugs without having to remove from wall and resolder UART
debug = True

# Load config file from disk
with open('config.json', 'r') as file:
    config = json.load(file)



def startup(arg="unused"):
    # Turn onboard LED on, indicates setup in progress
    led = Pin(13, Pin.OUT, value=0)

    # Connect to wifi
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

    # If urequests module not installed (esp8266 binaries), install it
    try:
        import urequests
    except:
        import upip
        upip.install('micropython-urequests')
        import urequests

    # Get offset for current timezone
    # Got traceback on this line, OSError: -202 - add try/except
    response = urequests.get("http://api.timezonedb.com/v2.1/get-time-zone?key=N49YL8DI5IDS&format=json&by=zone&zone=America/Los_Angeles")
    global offset
    offset = response.json()["gmtOffset"]

    # Get sunrise/sunset time from API, returns class object
    response = urequests.get("https://api.sunrise-sunset.org/json?lat=45.524722&lng=-122.6771891")
    # Parse out sunrise/sunset, convert to 24h format
    global sunrise
    global sunset
    sunrise = convertTime(response.json()['results']['sunrise'])
    sunset = convertTime(response.json()['results']['sunset'])

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

    if not debug:
        # Disconnect from wifi to reduce power usage
        wlan.disconnect()
        wlan.active(False)

    ## Timer Interrupts ##

    # Get epoch time of next 3:00 am (re-run timestamp to epoch conversion)
    epoch = time.mktime(time.localtime()) + offset
    now = time.localtime(epoch)
    if now[3] < 3:
        next_reset = time.mktime((now[0], now[1], now[2], 3, 0, 0, now[6], now[7]))
    else:
        next_reset = time.mktime((now[0], now[1], now[2]+1, 3, 0, 0, now[6], now[7])) # In testing, only needed to increment day - other parameters roll over correctly

    # Set interrupt to re-run setup at 3:00 am (epoch times only work once, need to refresh daily)
    next_reset = (next_reset - epoch) * 1000
    api_timer.init(period=next_reset, mode=Timer.ONE_SHOT, callback=startup)



    # Get epoch time of next sunset (turn relay on)
    next_sunset = time.mktime((now[0], now[1], now[2], int(sunrise.split(":")[0]), int(sunrise.split(":")[1]), 0, now[6], now[7]))
    if epoch > next_sunset:
        next_sunset = time.mktime((now[0], now[1], now[2]+1, int(sunrise.split(":")[0]), int(sunrise.split(":")[1]), 0, now[6], now[7]))

    # Set interrupt to turn relay on at sunset
    next_sunset = (next_sunset - epoch) * 1000
    sunset_timer.init(period=next_sunset, mode=Timer.ONE_SHOT, callback=night)



    # Get epoch time of next sunrise (turn relay off)
    next_sunrise = time.mktime((now[0], now[1], now[2], int(sunrise.split(":")[0]), int(sunrise.split(":")[1]), 0, now[6], now[7]))
    if epoch > next_sunrise:
        next_sunrise = time.mktime((now[0], now[1], now[2]+1, int(sunrise.split(":")[0]), int(sunrise.split(":")[1]), 0, now[6], now[7]))

    # Set interrupt to turn relay off at sunrise
    next_sunrise = (next_sunrise - epoch) * 1000
    sunrise_timer.init(period=next_sunrise, mode=Timer.ONE_SHOT, callback=morning)



    # Turn off LED to confirm setup completed successfully
    led.value(1)



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



# Sunrise interrupt routine
def morning(pin):
    relay.value(0)

# Sunset interrupt routine
def night(pin):
    relay.value(1)

# Interrupt function - lets lightswitch override relay state
def switch_interrupt(pin):
    if switch.value():
        relay.value(0)
    elif not switch.value():
        relay.value(1)

# Call interrupt function when switch changes in either direction
switch.irq(trigger=Pin.IRQ_RISING, handler=switch_interrupt)
switch.irq(trigger=Pin.IRQ_FALLING, handler=switch_interrupt)

# Run startup
startup()

# Set initial state on boot (interrupts only run at sunrise/sunset)
epoch = time.mktime(time.localtime()) + offset
now = time.localtime(epoch)

# Just check hour since this will only run once after power outage anyway
if int(sunrise.split(":")[0]) <= now[3] < int(sunset.split(":")[0]):
    relay.value(0)
else:
    relay.value(1)


if debug:
    # Connect to wifi
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(config["wifi"]["ssid"], config["wifi"]["password"])
    webrepl.start()

    while True:
        if not os.stat("boot.py") == old:
            # If file changed (new code received from webrepl), reboot
            import machine
            print("\nReceived new code from webrepl, rebooting...\n")
            time.sleep(1) # Prevents webrepl_cli.py from hanging after upload (esp reboots too fast)
            machine.reset()
        else:
            time.sleep(1) # Allow receiving upload
