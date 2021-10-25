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

# Parameter isn't actually used, just has to accept one so it can be called by timer (passes itself as arg)
def startup(arg="unused"):
    # Turn onboard LED on, indicates setup in progress
    led = Pin(2, Pin.OUT, value=1)

    # Connect to wifi
    global wlan
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect('jamnet', 'cjZY8PTa4ZQ6S83A')

    # Get current time from internet - delay prevents hanging
    time.sleep(2)
    ntptime.settime()

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
        sock_tcp.send(encrypt(cmd))
        data = sock_tcp.recv(2048)
        sock_tcp.close()

        decrypted = decrypt(data[4:])

        print("Sent:     ", cmd)
        print("Received: ", decrypted)

    except:
        quit(f"Could not connect to host {ip}:{port}")


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

    # Start 5 minute timer, calls function that allows loop to run again
    # If motion is detected again this will be reset
    timer.init(period=300000, mode=Timer.ONE_SHOT, callback=resetTimer)



# Create interrupt, call handler function when motion detected
pir.irq(trigger=Pin.IRQ_RISING, handler=motion_detected)
# Call function when button pressed, used for uploading new code
button.irq(trigger=Pin.IRQ_RISING, handler=buttonInterrupt)



startup()

motion = False

while True:
    # wifi = False unless user presses interrupt button
    if not wifi:
        if not hold:
            if motion:
                print("motion detected")
                now = time.localtime() # Create tuple, param 3 = hour
                # Change timezone function in library is broken so stuck on GMT time
                # In Spring/Summer/Fall sunset is 12-4 am GMT, so the else conditional is used
                # In Winter sunset rolls over to 10-11 pm GMT, requiring 2 conditionals
                if sunset > sunrise:
                    if 0 <= now[3] <= sunrise or sunset <= now[3] <= 23: # If after sunset + before sunrise
                        if not lights:
                            send("192.168.1.206", 28, "dimmer")
                            send("192.168.1.225", 1, "bulb")
                            lights = True
                            hold = True
                    else:
                        if not lights:
                            send("192.168.1.206", 100, "dimmer")
                            send("192.168.1.225", 100, "bulb")
                            lights = True
                            hold = True
                else:
                    if sunset <= now[3] <= sunrise: # If after sunset + before sunrise
                        if not lights:
                            send("192.168.1.206", 28, "dimmer")
                            send("192.168.1.225", 1, "bulb")
                            lights = True
                            hold = True
                    else:
                        if not lights:
                            send("192.168.1.206", 100, "dimmer")
                            send("192.168.1.225", 100, "bulb")
                            lights = True
                            hold = True
            else:
                if lights:
                    send("192.168.1.206", 1, "dimmer")
                    send("192.168.1.225", 1, "bulb", 0)
                    lights = False
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
