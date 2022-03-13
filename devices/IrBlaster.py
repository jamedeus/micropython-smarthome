from ir_tx import Player
from machine import Pin
import json
import time
import logging

# Set name for module's log lines
log = logging.getLogger("IrBlaster")



class IrBlaster():
    def __init__(self, pin, target):
        led = Pin(pin, Pin.OUT, value = 0)
        self.ir = Player(led)
        self.target = target
        self.device_type = "ir_blaster"

        self.codes = {}

        if self.target == "tv":
            with open('samsung-codes.json', 'r') as file:
                self.codes["tv"] = json.load(file)

        elif self.target == "ac":
            with open('whynter-codes.json', 'r') as file:
                self.codes["ac"] = json.load(file)

        elif self.target == "both":
            with open('samsung-codes.json', 'r') as file:
                self.codes["tv"] = json.load(file)
            with open('whynter-codes.json', 'r') as file:
                self.codes["ac"] = json.load(file)

        log.info(f"Instantiated IrBlaster on pin {pin}")



    def send(self, dev, key):
        self.ir.play(self.codes[dev][key])



    def backlight(self, state):
        self.send("tv", "settings")
        time.sleep(2)
        self.send("tv", "right")
        time.sleep_ms(500)
        self.send("tv", "down")
        time.sleep_ms(500)
        self.send("tv", "enter")
        time.sleep_ms(500)

        ct = 1

        if state == "on":
            direction = "right"
        else:
            direction = "left"

        while ct < 15:
            self.send("tv", direction)
            time.sleep_ms(150)
            ct += 1

        self.send("tv", "exit")
