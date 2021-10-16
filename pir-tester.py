# This file is executed on every boot (including wake-boot from deepsleep)
#import esp
#esp.osdebug(None)

# Connect PIR motion sensor:
# VCC: 3v3
# GND: GND
# Data: D15 (GPIO 15)

import webrepl
import network
import time
from machine import Pin, PWM

# Connect to wifi
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect('jamnet', 'cjZY8PTa4ZQ6S83A')

# Start webrepl to allow connecting and uploading scripts over network
# Do not put code before this, if it hangs will not be able to connect
webrepl.start()

motion = False

# Interrupt routine, called when motion sensor triggered
def motion_detected(pin):
    global motion
    motion = True

# Onboard LED turns on when motion detected
led = Pin(2, Pin.OUT, value=0)

# Turn on LED strip when motion detected (if connected)
pwm = PWM(Pin(4), duty=0)

# PIR data pin connected to D15
pir = Pin(15, Pin.IN)

# Create interrupt, call handler function when motion detected
pir.irq(trigger=Pin.IRQ_RISING, handler=motion_detected)

while True:
    if motion:
        print("Motion detected")
        led.value(1)
        pwm.duty(1023)
        time.sleep(20)
        led.value(0)
        pwm.duty(0)
        motion = False
