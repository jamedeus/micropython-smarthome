# This file is executed on every boot (including wake-boot from deepsleep)
#import esp
#esp.osdebug(None)

import webrepl
import network
import time
import ntptime
from machine import Pin, PWM, Timer

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

# PIR data pin connected to D15
pir = Pin(15, Pin.IN)

# Used to set pwm duty cycle
bright = 0

# Hardware timer used to keep lights on for 5 min
timer = Timer(0)

# Stops the loop from running when True, hware timer resets after 5 min
hold = False
motion = False

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



def fade(state):
    global bright
    if state == "on":
        print(bright)
        while bright < 32:
            bright = bright + 1
            pwm.duty(bright)
            time.sleep_ms(32)

        # Prevent loop from running (keeps lights on)
        global hold
        hold = True

    elif state == "off":
        print(bright)
        while bright > 0:
            bright = bright - 1
            pwm.duty(bright)
            time.sleep_ms(32)



# Create interrupt, call handler function when motion detected
pir.irq(trigger=Pin.IRQ_RISING, handler=motion_detected)



while True:
    if not hold:
        if motion:
            now = time.localtime() # Create tuple, param 3 = hour
            if now[3] in range(2, 13): # From 7 pm to 6:59 am lights ON
                fade("on")
            else:
                motion = False
        else:
            fade("off")
        time.sleep_ms(20)
