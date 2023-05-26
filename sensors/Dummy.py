import logging
from Sensor import Sensor

# Set name for module's log lines
log = logging.getLogger("Dummy_Sensor")


class Dummy(Sensor):
    def __init__(self, name, nickname, _type, default_rule, targets):
        super().__init__(name, nickname, _type, True, None, default_rule, targets)

        log.info(f"Instantiated dummy sensor named {self.name}")

    # Accepts additional rules because they are the only factor determining if condition is met
    # With only enabled/disabled it would never turn targets off (condition not checked while disabled)
    def validator(self, rule):
        try:
            if rule.lower() == "on" or rule.lower() == "off":
                return rule.lower()
            else:
                return False
        except AttributeError:
            return False

    def condition_met(self):
        if self.current_rule == "on":
            return True
        elif self.current_rule == "off":
            return False
        else:
            return None
