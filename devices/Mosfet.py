from machine import Pin
from Device import Device
import logging

# Set name for module's log lines
log = logging.getLogger("Mosfet")



class Mosfet(Device):
    def __init__(self, name, nickname, device_type, enabled, current_rule, default_rule, pin):
        super().__init__(name, nickname, device_type, enabled, current_rule, default_rule)

        self.mosfet = Pin(pin, Pin.OUT, Pin.PULL_DOWN)

        log.info(f"Instantiated Mosfet named {self.name} on pin {pin}")



    def send(self, state=1):
        # Refuse to turn on while disabled
        if not self.enabled and state:
            return False

        self.mosfet.value(state)
        return True
