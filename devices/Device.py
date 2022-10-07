import logging

# Set name for module's log lines
log = logging.getLogger("Device")



class Device():
    def __init__(self, name, nickname, device_type, enabled, current_rule, default_rule):

        # Unique, sequential name (device1, device2, ...) used in backend
        self.name = name

        # User-configurable name used in frontend, not necesarily unique
        self.nickname = nickname

        self.device_type = device_type

        self.enabled = enabled

        # Record device's on/off state
        self.state = None

        # The rule actually followed when the device is triggered (can be changed through API)
        self.current_rule = current_rule

        # The rule that should be followed at the current time (used to undo API changes to current_rule)
        self.scheduled_rule = current_rule

        # The fallback rule used when no other valid rules are available
        # Can happen if config file contains invalid rules, or if enabled through API while both current and schedule rule are "disabled"
        self.default_rule = default_rule

        # Will hold sequential schedule rules so they can be quickly changed when interrupt runs
        self.rule_queue = []

        # Will be populated with instances of all triggering sensors later
        self.triggered_by = []



    def enable(self):
        self.enabled = True

        # Replace "disabled" with usable rule
        if self.current_rule == "disabled":
            # Revert to scheduled rule unless it is also "disabled"
            if not str(self.scheduled_rule).lower() == "disabled":
                self.current_rule = self.scheduled_rule
            # Last resort: revert to default_rule
            else:
                self.current_rule = self.default_rule

        # If other devices in group are on, turn on to match state
        try:
            if self.group.state == True:
                success = self.send(1)
                if success:
                    self.state = True
                else:
                    # Forces group to turn on again, retrying until successful (send command above likely failed due to temporary network error)
                    # Only used as last resort due to side effects - if user previously turned OFF a device in this group through API, then
                    # re-enables this device, group will turn BOTH on (but user only wanted to turn this one on)
                    self.group.state = False
        except AttributeError:
            pass



    def disable(self):
        # Turn off before disabling
        if self.state:
            self.send(0)
            self.state = False

        self.enabled = False



    # Base validator for universal rules, can be extended in subclass validator method
    def rule_validator(self, rule):
        if str(rule).lower() == "enabled" or str(rule).lower() == "disabled":
            return str(rule).lower()
        else:
            return self.validator(rule)



    # Placeholder function, intended to be overwritten by subclass validator method
    def validator(self, rule):
        return False



    def set_rule(self, rule):
        # Check if rule is valid using subclass method - may return a modified rule (ie cast str to int)
        valid_rule = self.rule_validator(rule)
        if not str(valid_rule) == "False":
            self.current_rule = valid_rule
            log.info(f"{self.name}: Rule changed to {self.current_rule}")
            print(f"{self.name}: Rule changed to {self.current_rule}")

            # Rule just changed to disabled
            if self.current_rule == "disabled":
                self.send(0)
                self.disable()
            # Rule just changed to enabled, replace with usable rule (default) and enable
            elif self.current_rule == "enabled":
                self.current_rule = self.default_rule
                self.enable()
            # Device was previously disabled, enable now that rule has changed
            elif self.enabled == False:
                self.enable()
            # Device is currently on, run send so new rule can take effect
            elif self.state == True:
                self.send(1)

            return True

        else:
            log.error(f"{self.name}: Failed to change rule to {rule}")
            print(f"{self.name}: Failed to change rule to {rule}")
            return False



    def next_rule(self):
        log.debug(f"{self.name}: Scheduled rule change")
        print(f"{self.name}: Scheduled rule change")
        if self.set_rule(self.rule_queue.pop(0)):
            # If new rule is valid, also change scheduled_rule
            self.scheduled_rule = self.current_rule
