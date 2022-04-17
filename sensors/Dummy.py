import logging
from Sensor import Sensor

# Set name for module's log lines
log = logging.getLogger("Dummy_Sensor")



class Dummy(Sensor):
    def __init__(self, name, sensor_type, enabled, current_rule, scheduled_rule, targets):
        super().__init__(name, sensor_type, enabled, current_rule, scheduled_rule, targets)

        log.info(f"Instantiated dummy sensor named {self.name}")



    def rule_validator(self, rule):
        if rule == "on" or rule == "off" or rule == "Disabled":
            return rule



    def condition_met(self):
        if self.current_rule == "on":
            return True
        elif self.current_rule == "off":
            return False
        else:
            return None
