# This file is executed on every boot (including wake-boot from deepsleep)
#import esp
#esp.osdebug(None)

import webrepl
import network
import time
import ntptime
from machine import Pin, PWM

# Connect to wifi
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect('jamnet', 'cjZY8PTa4ZQ6S83A')

# Start webrepl to allow connecting and uploading scripts over network
# Do not put code before this, if it hangs will not be able to connect
webrepl.start()

# Turn onboard LED on
led = Pin(2, Pin.OUT, value=1)

# Get current time from internet - delay prevents hanging
time.sleep(2)
ntptime.settime()

# Turn off LED to confirm time was set
led.value(0)

# PWM pin for LED strip
pwm = PWM(Pin(4), duty=0)

# Used to set pwm duty cycle
bright = 0



def fade(state):
    global bright
    if state == "on":
        while bright <= 32:
            pwm.duty(bright)
            bright = bright + 1
            time.sleep_ms(32)
    else:
        while bright >= 0:
            pwm.duty(bright)
            bright = bright - 1
            time.sleep_ms(32)



while True:
    now = time.localtime() # Create tuple, param 3 = hour
    if now[3] in range(6, 9): # From 11 pm to 2:59 am lights ON
        fade("on")
    elif now[3] in range(10, 23) or now[3] in range(0, 5): # From 3 am to 10:59 pm lights OFF
        fade("off")
    time.sleep(5) # Check every 5 seconds
