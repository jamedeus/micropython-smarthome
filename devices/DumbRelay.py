import logging
from machine import Pin
from Device import Device

# Set name for module's log lines
log = logging.getLogger("DumbRelay")



# Used for Sonoff relays running Tasmota
class DumbRelay(Device):
    def __init__(self, name, device_type, enabled, current_rule, scheduled_rule, pin):
        super().__init__(name, device_type, enabled, current_rule, scheduled_rule)

        self.relay = Pin(pin, Pin.OUT)

        log.info(f"Instantiated Relay named {self.name} on pin {pin}")



    def rule_validator(self, rule):
        if rule == "on" or rule == "off" or rule == "Disabled":
            return rule
        else:
            return False



    def send(self, state=1):
        log.info(f"{self.name}: send method called, state = {state}")

        if self.current_rule == "off" and state == 1:
            return True # Tell sensor that send succeeded so it doesn't retry forever
        else:
            self.relay.value(state)
            return True
