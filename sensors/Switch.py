# This module can be used with reed switches, toggle switches, push buttons, etc.
# Connect the switch with a ohm resister in series between an input pin and 3.3v pin

import logging
from Sensor import Sensor
from machine import Pin

# Set name for module's log lines
log = logging.getLogger("Switch_Sensor")



class Switch(Sensor):
    def __init__(self, name, nickname, sensor_type, enabled, current_rule, default_rule, targets, pin):
        super().__init__(name, nickname, sensor_type, enabled, current_rule, default_rule, targets)

        self.switch = switch = Pin(pin, Pin.IN, Pin.PULL_DOWN)

        log.info(f"Instantiated switch sensor named {self.name}")



    def rule_validator(self, rule):
        try:
            if rule.lower() == "enabled" or rule.lower() == "disabled":
                return rule.lower()
            else:
                return False
        except AttributeError:
            return False



    def condition_met(self):
        if self.switch.value():
            return True
        else:
            return False
