import time
import logging
from machine import Pin
from ir_tx import Player

# Set name for module's log lines
log = logging.getLogger("IrBlaster")


class IrBlaster():
    def __init__(self, pin, target):
        led = Pin(int(pin), Pin.OUT, value=0)
        self.ir = Player(led)
        self.target = target
        self._type = "ir_blaster"

        self.codes = {}

        if "tv" in self.target:
            from ir_codes import samsung
            self.codes["tv"] = samsung

        if "ac" in self.target:
            from ir_codes import whynter
            self.codes["ac"] = whynter

        log.info(f"Instantiated IrBlaster on pin {pin}")

    def send(self, dev, key):
        try:
            self.ir.play(self.codes[dev.lower()][key.lower()])
            return True
        except (KeyError, AttributeError):
            return False

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
