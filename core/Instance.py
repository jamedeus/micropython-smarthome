import logging

# Set name for module's log lines
log = logging.getLogger("Instance")


# Base class inherited by Device and Sensor subclasses
class Instance():
    def __init__(self, name, nickname, _type, enabled, current_rule, default_rule):

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

        # Will hold sequential schedule rules so they can be quickly changed when interrupt runs
        self.rule_queue = []

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

    def set_rule(self, rule):
        # Check if rule is valid using subclass method - may return a modified rule (ie cast str to int)
        valid_rule = self.rule_validator(rule)
        if not str(valid_rule) == "False":
            self.current_rule = valid_rule
            log.info(f"{self.name}: Rule changed to {self.current_rule}")
            print(f"{self.name}: Rule changed to {self.current_rule}")

            # Update instance attributes to reflect new rule
            # This method must be implemented by subclasses
            self.apply_new_rule()

            return True

        else:
            log.error(f"{self.name}: Failed to change rule to {rule}")
            print(f"{self.name}: Failed to change rule to {rule}")
            return False

    # Placeholder function, intended to be overwritten by subclass apply_new_rule method
    def apply_new_rule(self):
        pass

    # Base validator for universal rules, can be extended in subclass validator method
    def rule_validator(self, rule):
        if str(rule).lower() == "enabled" or str(rule).lower() == "disabled":
            return str(rule).lower()
        else:
            return self.validator(rule)

    # Placeholder function, intended to be overwritten by subclass validator method
    def validator(self, rule):
        return False

    # Called by SoftwareTimer tasks at each scheduled rule change
    def next_rule(self):
        log.debug(f"{self.name}: Scheduled rule change")
        print(f"{self.name}: Scheduled rule change")
        if self.set_rule(self.rule_queue.pop(0)):
            # If new rule is valid, also change scheduled_rule
            self.scheduled_rule = self.current_rule

    # Return JSON-serializable dict containing all current attributes
    # Called by API get_attributes endpoint
    def get_attributes(self):
        attributes = self.__dict__.copy()

        # Replace group object with group name (JSON-compatibility)
        if "group" in self.__dict__:
            attributes["group"] = self.group.name

        return attributes

    # Return JSON-serializable dict containing state information
    # Called by Config.get_status to build API status response
    def get_status(self):
        return {
            'nickname': self.nickname,
            'type': self._type,
            'enabled': self.enabled,
            'current_rule': self.current_rule,
            'scheduled_rule': self.scheduled_rule
        }
