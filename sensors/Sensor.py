import logging

# Set name for module's log lines
log = logging.getLogger("Sensor")


class Sensor():
    def __init__(self, name, nickname, _type, enabled, current_rule, default_rule, targets):

        # Unique, sequential name (sensor1, sensor2, ...) used in backend
        self.name = name

        # User-configurable name used in frontend, not necesarily unique
        self.nickname = nickname

        self._type = _type

        self.enabled = enabled

        # The rule actually followed when the device is triggered (can be changed through API)
        self.current_rule = current_rule

        # The rule that should be followed at the current time (used to undo API changes to current_rule)
        self.scheduled_rule = current_rule

        # The fallback rule used when no other valid rules are available
        # Examples: Config file contains invalid rules, enabled while both current + scheduled rules are "disabled"
        self.default_rule = default_rule

        # Prevent instantiating with invalid default_rule
        if self._type in ("pir", "si7021", "dummy") and str(self.default_rule).lower() in ("enabled", "disabled"):
            log.critical(f"{self.name}: Received invalid default_rule: {self.default_rule}")
            raise AttributeError

        # Will hold sequential schedule rules so they can be quickly changed when interrupt runs
        self.rule_queue = []

        # List of instances
        self.targets = targets

    def refresh_group(self):
        # Check conditions of all sensors in group
        if hasattr(self, 'group'):
            print(f"{self.name}: Refreshing {self.group.name}")
            self.group.refresh()

    def enable(self):
        self.enabled = True

        # Replace "disabled" with usable rule
        if self.current_rule == "disabled":
            # Revert to scheduled rule unless it is also "disabled"
            if not str(self.scheduled_rule).lower() == "disabled":
                self.set_rule(self.scheduled_rule)
            # Last resort: revert to default_rule
            else:
                self.set_rule(self.default_rule)

        # Check conditions of all sensors in group
        self.refresh_group()

    def disable(self):
        self.enabled = False

        # Check conditions of all sensors in group
        self.refresh_group()

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
                # TODO there are probably scenarios where lights can get stuck on here
                self.disable()
            # Rule just changed to enabled, replace with usable rule (default) and enable
            elif self.current_rule == "enabled":
                self.current_rule = self.default_rule
                self.enable()
            # Sensor was previously disabled, enable now that rule has changed
            elif self.enabled is False:
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
        if self._type == "pir":
            self.motion_detected()
            return True

        elif self._type == "desktop":
            self.current = "On"
            self.refresh_group()
            return True

        elif self._type == "si7021":
            return False

        elif self._type == "dummy":
            self.set_rule("on")
            return True

        elif self._type == "switch":
            return False

    # Called by Config after adding Sensor to Group. Appends functions to Group's post_action_routines list
    # Placeholder function for subclasses with no post-routines, overwritten if they do
    def add_routines(self):
        return

    # Return JSON-serializable dict containing all current attributes
    # Called by API get_attributes endpoint
    def get_attributes(self):
        attributes = self.__dict__.copy()

        # Make dict json-compatible
        for i in self.__dict__:
            # Remove object references
            if i in ("i2c", "temp_sensor", "sensor", "switch"):
                del attributes[i]

            # Replace desktop_target instance with instance.name
            elif i == "desktop_target":
                if attributes["desktop_target"] is not None:
                    attributes["desktop_target"] = attributes["desktop_target"].name

            # Replace monitor_task with True or False
            elif i == "monitor_task":
                if attributes["monitor_task"] is not None:
                    attributes["monitor_task"] = True
                else:
                    attributes["monitor_task"] = False

            # Replace group object with group name
            elif i == "group":
                attributes["group"] = self.group.name

        # Replace device instances with instance.name attribute
        attributes["targets"] = []
        for i in self.targets:
            attributes["targets"].append(i.name)

        return attributes
