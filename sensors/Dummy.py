from Sensor import Sensor


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
      default_rule: Fallback rule used when no other valid rules are available
      schedule:     Dict with timestamps/keywords as keys, rules as values
      targets:      List of device names (device1 etc) controlled by sensor

    Supports universal rules ("enabled" and "disabled") as well as "on" and
    "off". The condition_met method will always return True when rule is "on"
    and always return False when rule is "off".
    The default_rule must be "on" or "off" (not universal rule).
    '''

    def __init__(self, name, nickname, _type, default_rule, schedule, targets):
        super().__init__(name, nickname, _type, True, default_rule, schedule, targets)

        # Prevent instantiating with invalid default_rule
        if str(self.default_rule).lower() in ("enabled", "disabled"):
            self.log.critical("Invalid default_rule: %s", self.default_rule)
            raise AttributeError

        self.log.info("Instantiated")

    def validator(self, rule):
        '''Accepts "on" and "off", rejects all other rules.'''

        try:
            if rule.lower() in ["on", "off"]:
                return rule.lower()
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

        # Refresh group if rule changed successfully
        if super().set_rule(rule, scheduled):
            self.refresh_group()
            return True
        return False

    def condition_met(self):
        '''Returns True if current_rule is "on" (turn target devices on).
        Returns False if current_rule is "off" (turn target devices off).
        Returns None if current_rule is enabled or disabled (no effect).
        '''

        if self.current_rule == "on":
            return True
        if self.current_rule == "off":
            return False
        return None

    def trigger(self):
        '''Called by trigger_sensor API endpoint, sets current_rule to "on"
        (turns on target devices). Rule must be changed or sensor disabled to
        turn target devices off (will stay on forever while rule is "on").
        '''
        self.log.debug("trigger method called")
        self.set_rule("on")
        return True
