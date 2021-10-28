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
import ntptime

# Connect to wifi
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

# Start webrepl to allow connecting and uploading scripts over network
# Do not put code before this, if it hangs will not be able to connect
webrepl.start()

motion = False

# Interrupt routine, called when motion sensor triggered
def motion_detected(pin):
    global motion
    motion = True

# Button intterupt callback
def buttonInterrupt(pin):
    global wifi
    wifi = True

# Onboard LED turns on when motion detected
led = Pin(2, Pin.OUT, value=0)

# Turn on LED strip when motion detected (if connected)
pwm = PWM(Pin(4), duty=0)

# PIR data pin connected to D15
pir = Pin(15, Pin.IN)

# Create interrupt, call handler function when motion detected
pir.irq(trigger=Pin.IRQ_RISING, handler=motion_detected)

# Interrupt button, breaks loop, waits for file upload then automatically reboots
button = Pin(16, Pin.IN)
button.irq(trigger=Pin.IRQ_RISING, handler=buttonInterrupt)

# Set to True by interrupt button
wifi = False

# If True, onboard LED and PWM light will blink when motion detected
# Disabled by default because the delay sometimes prevents a few log messages
blink = False

# If True, output timestamps when motion detected to log file
# Useful for extended testing (cannot scrollback in screen/webrepl)
log = True

# Makes it easier to manually open log from screen/webrepl
def view_log():
    log = open('log.txt', 'r').read()
    print()
    print(log)

    choice = input("Enter \"delete\" to clear the log: ")
    if choice == "delete":
        import os
        os.remove('log.txt')
        print("Log deleted")
    else:
        print("Log kept")



while True:
    if not wifi:
        if motion:
            # Get time tuple
            now = time.localtime()

            # Create string, timestamp added in loop
            log = "Motion detected at "

            # Since tuple contains int not str, single digit hour/min/sec lack leading 0s
            # For readability, check length of each and add leading 0 if single-digit
            for i in range(3,6):
                if len(str(now[i])) == 1:
                    log = log + "0" + str(now[i]) + ":"
                else:
                    log = log + str(now[i]) + ":"
            else:
                log = log[0:-1] # Remove trailing : added by loop

            # Print to console for real-time monitoring
            print(log)

            if log:
                file = open('log.txt', 'a')
                file.write(log + "\n") # Append to log with newline after
                file.close() # Unlike CPython, nothing is written until file closed

            if blink:
                led.value(1)
                pwm.duty(1023)
                time.sleep_ms(25)
                led.value(0)
                pwm.duty(0)

            motion = False
    else:
        # Runs when interrupt button pressed, wait for webrepl upload then reboot automatically
        led.value(1)
        print("maintenance mode")
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
