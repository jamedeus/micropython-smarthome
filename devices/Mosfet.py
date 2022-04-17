from machine import Pin
from Device import Device
import logging

# Set name for module's log lines
log = logging.getLogger("Mosfet")



class Mosfet(Device):
    def __init__(self, name, device_type, enabled, current_rule, scheduled_rule, pin):
        super().__init__(name, device_type, enabled, current_rule, scheduled_rule)

        self.mosfet = Pin(pin, Pin.OUT, Pin.PULL_DOWN)

        log.info(f"Instantiated Mosfet named {self.name} on pin {pin}")



    def rule_validator(self, rule):
        if rule == "on" or rule == "off" or rule == "Disabled":
            return rule
        else:
            return False



    def send(self, state=1):
        if self.current_rule == "off" and state == 1:
            pass
        else:
            self.mosfet.value(state)

        return True
