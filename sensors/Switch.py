# This module can be used with reed switches, toggle switches, push buttons, etc.
# Connect the switch with a ohm resister in series between an input pin and 3.3v pin

import logging
from machine import Pin
from Sensor import Sensor

# Set name for module's log lines
log = logging.getLogger("Switch_Sensor")


class Switch(Sensor):
    def __init__(self, name, nickname, _type, default_rule, targets, pin):
        super().__init__(name, nickname, _type, True, None, default_rule, targets)

        self.switch = Pin(int(pin), Pin.IN, Pin.PULL_DOWN)

        # Create hardware interrupt, refresh group when switch changes state
        self.switch.irq(handler=self.interrupt_handler, trigger=Pin.IRQ_FALLING | Pin.IRQ_RISING)

        log.info(f"Instantiated switch sensor named {self.name}")

    # Called by hardware intterupt, must accept arg (unused)
    # Refresh group when switch changes state
    def interrupt_handler(self, arg=None):
        self.refresh_group()

    def condition_met(self):
        if self.switch.value():
            return True
        else:
            return False
