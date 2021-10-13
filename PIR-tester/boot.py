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
from machine import Pin

# Interrupt routine, called when motion sensor triggered
def motion_detected(pin):
    print("Motion detected")
    led.value(1)
    time.sleep_ms(250)
    led.value(0)

# Connect to wifi
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect('jamnet', 'cjZY8PTa4ZQ6S83A')

# Start webrepl to allow connecting and uploading scripts from browser
webrepl.start()

# Onboard LED blinks when motion detected
led = Pin(2, Pin.OUT)
led.value(0)

# PIR data pin connected to D15
pir = Pin(15, Pin.IN, Pin.PULL_DOWN)
# Create interrupt, call handler function when motion detected
pir.irq(trigger=Pin.IRQ_RISING, handler=motion_detected)
