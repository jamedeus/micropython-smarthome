import logging
from util import print_with_timestamp

# Set name for module's log lines
log = logging.getLogger("Instance")


# Base class inherited by Device and Sensor subclasses
class Instance():
    def __init__(self, name, nickname, _type, enabled, current_rule, default_rule):

        # Unique, sequential name (sensor1, sensor2, ...) used in backend
        self.name = name

        # User-configurable name used in frontend, not necessarily unique
        self.nickname = nickname

        # Instance type, arg determines which class is instantiated by Config.instantiate_hardware
        # Attribute is used in status object, determines UI shown by frontend
        self._type = _type

        # Bool, set with enable/disable methods
        # Determines whether instance affects other instances in group
        self.enabled = enabled

        # The rule currently being followed, has different effects depending on subclass
        # - Devices: determines whether device can be turned on, device brightness, etc
        # - Sensors: determines how sensor is triggered, how long before sensor resets, etc
        self.current_rule = current_rule

        # The rule that should be followed at the current time unless changed by API
        # The reset_rule endpoint overwrites current_rule with this rule
        # This rule will be set when a disabled instance is re-enabled
        self.scheduled_rule = current_rule

        # The fallback rule used when no other valid rules are available, examples:
        # - Config file contains invalid schedule rules
        # - Instance enabled while both current and scheduled rules are "disabled"
        self.default_rule = default_rule

        # Stores sequential schedule rules, next_rule method applies the first rule in queue
        # Config.build_queue populates list + adds callback timers for each rule change
        self.rule_queue = []

    def enable(self):
        self.enabled = True

        # Replace "disabled" with usable rule
        if self.current_rule == "disabled":
            # Revert to scheduled rule unless it is also "disabled"
            if str(self.scheduled_rule).lower() != "disabled":
                self.set_rule(self.scheduled_rule)
            # Last resort: revert to default_rule
            else:
                self.set_rule(self.default_rule)

    def disable(self):
        self.enabled = False

    # Takes rule, validates, sets current_rule if valid
    # Also sets scheduled_rule if scheduled arg is True
    def set_rule(self, rule, scheduled=False):
        # Check if rule is valid (may return modified rule, eg cast str to int)
        valid_rule = self.rule_validator(rule)
        if valid_rule is not False:
            self.current_rule = valid_rule
            # If called by next_rule: set scheduled_rule
            if scheduled:
                self.scheduled_rule = valid_rule
            log.info(f"{self.name}: Rule changed to {self.current_rule}")
            self.print(f"Rule changed to {self.current_rule}")

            # Update instance attributes to reflect new rule
            self.apply_new_rule()

            return True

        else:
            log.error(f"{self.name}: Failed to change rule to {rule}")
            self.print(f"Failed to change rule to {rule}")
            return False

    # Called by set_rule, updates instance attributes to reflect new rule
    # Can be extended in subclass (example: devices call send method)
    def apply_new_rule(self):
        # Rule just changed to disabled
        if self.current_rule == "disabled":
            self.disable()
        # Rule just changed to enabled, replace with usable rule and enable
        elif self.current_rule == "enabled":
            # Use scheduled_rule unless also unusable, otherwise default_rule
            if str(self.scheduled_rule).lower() not in ["enabled", "disabled"]:
                self.current_rule = self.scheduled_rule
            else:
                self.current_rule = self.default_rule
            self.enable()
        # Instance was previously disabled, enable now that rule has changed
        elif self.enabled is False:
            self.enable()

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
        self.print("Scheduled rule change")
        self.set_rule(self.rule_queue.pop(0), True)

    # Return JSON-serializable dict containing all current attributes
    # Called by API get_attributes endpoint, more verbose than status
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
            'scheduled_rule': self.scheduled_rule,
            'default_rule': self.default_rule
        }

    # Takes string, prints with prepended timestamp and instance name
    def print(self, msg):
        print_with_timestamp(f"{self.name}: {msg}")
