import logging
from machine import Pin
from Device import Device

# Set name for module's log lines
log = logging.getLogger("DumbRelay")



# Used for relay breakout board
class DumbRelay(Device):
    def __init__(self, name, nickname, device_type, enabled, current_rule, default_rule, pin):
        super().__init__(name, nickname, device_type, enabled, current_rule, default_rule)

        self.relay = Pin(pin, Pin.OUT)

        log.info(f"Instantiated Relay named {self.name} on pin {pin}")



    def rule_validator(self, rule):
        try:
            if rule.lower() == "on" or rule.lower() == "off" or rule.lower() == "disabled":
                return rule.lower()
            else:
                return False
        except AttributeError:
            return False



    def send(self, state=1):
        log.info(f"{self.name}: send method called, state = {state}")

        if self.current_rule == "off" and state == 1:
            pass
        else:
            self.relay.value(state)

        return True
