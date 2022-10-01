import logging

# Set name for module's log lines
log = logging.getLogger("Sensor")



class Sensor():
    def __init__(self, name, nickname, sensor_type, enabled, current_rule, default_rule, targets):

        # Unique, sequential name (sensor1, sensor2, ...) used in backend
        self.name = name

        # User-configurable name used in frontend, not necesarily unique
        self.nickname = nickname

        self.sensor_type = sensor_type

        self.enabled = enabled

        # The rule actually followed when the device is triggered (can be changed through API)
        self.current_rule = current_rule

        # The rule that should be followed at the current time (used to undo API changes to current_rule)
        self.scheduled_rule = current_rule

        # The fallback rule used when no other valid rules are available
        # Can happen if config file contains invalid rules, or if enabled through API while both current and schedule rule are "disabled"
        self.default_rule = default_rule

        # Will hold sequential schedule rules so they can be quickly changed when interrupt runs
        self.rule_queue = []

        # List of instances
        self.targets = targets



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



    def disable(self):
        self.enabled = False



    def set_rule(self, rule):
        # Check if rule is valid using subclass method - may return a modified rule (ie cast str to int)
        valid_rule = self.rule_validator(rule)
        if not str(valid_rule) == "False":
            self.current_rule = valid_rule
            log.info(f"{self.name}: Rule changed to {self.current_rule}")
            print(f"{self.name}: Rule changed to {self.current_rule}")

            # Rule just changed to disabled
            if self.current_rule == "disabled":
                # TODO there are probably scenarios where lights can get stuck on here
                self.disable()
            # Sensor was previously disabled, enable now that rule has changed
            elif self.enabled == False:
                self.enable()

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



    # Allow API commands to simulate the sensor being triggered
    def trigger(self):
        if self.sensor_type == "pir":
            self.motion_detected()
            return True

        elif self.sensor_type == "desktop":
            self.current = "On"
            return True

        elif self.sensor_type == "si7021":
            return False

        elif self.sensor_type == "dummy":
            self.current_rule = "on"
            return True

        elif self.sensor_type == "switch":
            return False



    # Called by Config after adding Sensor to Group. Appends functions to Group's post_action_routines list
    # Placeholder function for subclasses with no post-routines, overwritten if they do
    def add_routines(self):
        return
