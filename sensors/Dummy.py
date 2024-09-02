import logging
from Sensor import Sensor

# Set name for module's log lines
log = logging.getLogger("Dummy_Sensor")


class Dummy(Sensor):
    '''Software-only sensor driver that keeps target devices turned on while
    current_rule is "on". Intended to be configured with schedule rules to keep
    devices on during certain times of day. Can be used as a sunrise or sunset
    sensor by creating schedule rules with the sunrise and sunset keywords.

    Args:
      name:         Unique, sequential config name (sensor1, sensor2, etc)
      nickname:     User-configured friendly name shown on frontend
      _type:        Instance type, determines driver class and frontend UI
      enabled:      Initial enable state (True or False)
      current_rule: Initial rule, has different effects depending on subclass
      default_rule: Fallback rule used when no other valid rules are available
      targets:      List of device names (device1 etc) controlled by sensor

    Supports universal rules ("enabled" and "disabled") as well as "on" and
    "off". The condition_met method will always return True when rule is "on"
    and always return False when rule is "off".
    The default_rule must be "on" or "off" (not universal rule).
    '''

    def __init__(self, name, nickname, _type, default_rule, targets):
        super().__init__(name, nickname, _type, True, None, default_rule, targets)

        # Prevent instantiating with invalid default_rule
        if str(self.default_rule).lower() in ("enabled", "disabled"):
            log.critical(f"{self.name}: Received invalid default_rule: {self.default_rule}")
            raise AttributeError

        log.info(f"Instantiated dummy sensor named {self.name}")

    def validator(self, rule):
        '''Accepts "on" and "off", rejects all other rules.'''

        try:
            if rule.lower() == "on" or rule.lower() == "off":
                return rule.lower()
            else:
                return False
        except AttributeError:
            return False

    def set_rule(self, rule, scheduled=False):
        '''Takes new rule, validates, if valid sets as current_rule (and
        scheduled_rule if scheduled arg is True) and calls apply_new_rule.

        Args:
          rule:      The new rule, will be set as current_rule if valid
          scheduled: Optional, if True also sets scheduled_rule if rule valid
        '''

        result = super().set_rule(rule)
        # Refresh group if rule changed successfully
        if result and hasattr(self, "group"):
            self.refresh_group()
        return result

    def condition_met(self):
        '''Returns True if current_rule is "on" (turn target devices on).
        Returns False if current_rule is "off" (turn target devices off).
        Returns None if current_rule is enabled or disabled (no effect).
        '''

        if self.current_rule == "on":
            return True
        elif self.current_rule == "off":
            return False
        else:
            return None

    def trigger(self):
        '''Called by trigger_sensor API endpoint, sets current_rule to "on"
        (turns on target devices). Rule must be changed or sensor disabled to
        turn target devices off (will stay on forever while rule is "on").
        '''
        self.set_rule("on")
        return True
