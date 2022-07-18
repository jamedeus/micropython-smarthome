import logging

# Set name for module's log lines
log = logging.getLogger("Device")



class Device():
    def __init__(self, name, device_type, enabled, current_rule, scheduled_rule):

        self.name = name

        self.device_type = device_type

        self.enabled = enabled

        # Record device's on/off state
        self.state = None

        # The rule actually followed when the device is triggered (can be changed through API)
        self.current_rule = current_rule

        # The rule that should be followed at the current time (used to undo API changes to current_rule)
        self.scheduled_rule = scheduled_rule

        # Will hold sequential schedule rules so they can be quickly changed when interrupt runs
        self.rule_queue = []

        # Will be populated with instances of all triggering sensors later
        self.triggered_by = []



    def enable(self):
        self.enabled = True

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
        self.enabled = False
        self.state = False



    def set_rule(self, rule):
        # Check if rule is valid using subclass method - may return a modified rule (ie cast str to int)
        valid_rule = self.rule_validator(rule)
        if not str(valid_rule) == "False":
            self.current_rule = valid_rule
            log.info(f"{self.name}: Rule changed to {self.current_rule}")
            print(f"{self.name}: Rule changed to {self.current_rule}")

            # Rule just changed to disabled
            if self.current_rule == "Disabled":
                self.send(0)
                self.disable()
            # Sensor was previously disabled, enable now that rule has changed
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
