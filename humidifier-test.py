import webrepl
import network
import time
from machine import Pin, Timer, RTC, SoftI2C
import socket
from struct import pack
import json
import os
import _thread



wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect('jamnet', 'cjZY8PTa4ZQ6S83A')

while not wlan.isconnected():
    continue

webrepl.start()



class Humidifier():
    def __init__(self, name, button_pin, level_pins, empty_pin):
        # Name is just for metadata
        # button_pin is the one connected to transistor which emulates capacitive touch
        # level_pins is a tuple of 3 values - each pin is connected to an indicator LED (low, med, high setting)
        # empty_pin is connected to the red LED that blinks when out of water
        self.name = name

        self.button = Pin(button_pin, Pin.OUT, Pin.PULL_DOWN)

        self.on_low = Pin(level_pins[0], Pin.IN)
        self.on_med = Pin(level_pins[1], Pin.IN)
        self.on_hi = Pin(level_pins[2], Pin.IN)

        self.empty = False
        self.empty_pin = Pin(empty_pin, Pin.IN)
        self.empty_pin.irq(trigger=Pin.IRQ_FALLING, handler=falling)

        # Will be 0 for off, 1 for low, 2 for med, 3 for hi setting
        self.status = 0

        # Used to detect when empty light is blinking
        self.interrupted = False

        _thread.start_new_thread(self.loop, ())



    def simulate_button(self):
        self.button.value(1)
        time.sleep_ms(10)
        self.button.value(0)



    # Called by interrupt when empty light is blinking
    def falling(pin):
        self.interrupted = True



    def loop(self):
        while True:
            if not self.on_low.value():
                self.status = 1
                led = Pin(2, Pin.OUT, value=0)
            elif not self.on_med.value():
                self.status = 2
                led = Pin(2, Pin.OUT, value=1)
            elif not self.on_hi.value():
                self.status = 3
                led = Pin(2, Pin.OUT, value=0)
            else:
                self.status = 0
                led = Pin(2, Pin.OUT, value=0)

            # Boolean set to True when red empty light blinks (interrupt)
            if self.interrupted:
                self.empty = True
                while True:
                    # Set to False, then wait 2 seconds - if light is blinking it will be flipped back
                    self.interrupted = False
                    time.sleep(2)

                    # If light still blinking, stay in loop (all functions disabled until refilled anyway)
                    if interrupted:
                        continue
                    # Once light quits blinking, set reset empty and break
                    else:
                        self.empty = False
                        break

            time.sleep(1)



# TODO remove below here after testing

instance = Humidifier("humidifier", 27, (33, 32, 35), 34)

def remote():
    # Create socket listening on port 4200
    s = socket.socket()
    s.bind(('', 4200))
    s.listen(1)

    # Handle connections
    while True:
        # Accept connection, decode message
        conn, addr = s.accept()
        msg = conn.recv(8).decode()

        if msg == "on":
            instance.simulate_button()

        # Close connection, restart loop and wait for next connection
        conn.close()


_thread.start_new_thread(remote, ())
