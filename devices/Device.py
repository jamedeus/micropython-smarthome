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

        # Enable self in sensor's targets dict
        for sensor in self.triggered_by:

            # Run loop again immediately so newly-enabled device acquires same on/off state as other devices
            if sensor.sensor_type == "pir":
                if sensor.motion:
                    self.state = False
                else:
                    self.state = True



    def disable(self):
        self.enabled = False



    def set_rule(self, rule):
        # Check if rule is valid using subclass method - may return a modified rule (ie cast str to int)
        rule = self.rule_validator(rule)
        if not str(rule) == "False":
            self.current_rule = rule
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
