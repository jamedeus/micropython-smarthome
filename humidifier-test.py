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

        self.empty_pin = Pin(empty_pin, Pin.IN)
        self.empty = False

        # Will be 0 for off, 1 for low, 2 for med, 3 for hi setting
        self.status = 0

        _thread.start_new_thread(self.loop, ())



    def simulate_button(self):
        self.button.value(1)
        time.sleep_ms(10)
        self.button.value(0)



    def loop(self):
        while True:
            if self.on_low.value():
                self.status = 1
            elif self.on_med.value():
                self.status = 2
            elif self.on_hi.value():
                self.status = 3
            else:
                self.status = 0

            if self.empty_pin.value():
                self.empty = True
            else:
                self.empty = False

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
