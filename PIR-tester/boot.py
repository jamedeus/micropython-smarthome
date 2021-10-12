# This file is executed on every boot (including wake-boot from deepsleep)
#import esp
#esp.osdebug(None)

# Connect PIR motion sensor:
# VCC: 3v3
# GND: GND
# Data: D2 (GPIO 2)

import webrepl
import network
import time
from machine import Pin

# Connect to wifi
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect('jamnet', 'cjZY8PTa4ZQ6S83A')

# Start webrepl to allow connecting and uploading scripts from browser
webrepl.start()

# PIR data pin connected to D2
pir = Pin(2, Pin.IN)

while True:
    if pir.value():
        print("Motion detected")
        print(pir.value())
    else:
        print("No motion")
        print(pir.value())
    time.sleep(1)
