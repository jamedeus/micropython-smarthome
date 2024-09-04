import logging
from util import print_with_timestamp

# Set name for module's log lines
log = logging.getLogger("Instance")


class Instance():
    '''Base class for all device and sensor drivers, implements universal API
    methods and attributes used to configure instance status, rules, etc.

    Args:
      name:         Unique, sequential config name (device1, sensor3, etc)
      nickname:     User-configured friendly name shown on frontend
      _type:        Instance type, determines driver class and frontend UI
      enabled:      Initial enable state (True or False)
      default_rule: Fallback rule used when no other valid rules are available

    Subclassed by the Device and Sensor base classes which implement functions
    specific to devices (lights, relays, etc) and sensors (sensors which turn
    devices on and off in response to certain conditions).

    Supports universal rules ("enabled" and "disabled"). Additional rules can
    be supported by replacing the validator method in subclass.
    '''

    def __init__(self, name, nickname, _type, enabled, default_rule):

        # Unique, sequential name (sensor1, sensor2, ...) used in backend
        self.name = name

        # User-configurable name used in frontend
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
        self.current_rule = None

        # The rule that should be followed at the current time unless changed by API
        # The reset_rule endpoint overwrites current_rule with this rule
        # This rule will be set when a disabled instance is re-enabled
        self.scheduled_rule = None

        # The fallback rule used when no other valid rules are available, examples:
        # - Config file contains invalid schedule rules
        # - Instance enabled while both current and scheduled rules are "disabled"
        self.default_rule = default_rule

        # Stores reference to Group instance (set by Config.build_groups)
        # Groups contain device(s) and sensor(s) that target them (devices turn
        # on when >=1 sensor condition is met, off when no conditions are met)
        self.group = None

        # Stores sequential schedule rules, next_rule method applies the first rule in queue
        # Config.build_queue populates list + adds callback timers for each rule change
        self.rule_queue = []

    def enable(self):
        '''Sets enabled bool to True (allows sensors to be checked, devices to
        be turned on/off), and ensures current_rule contains a usable value.
        '''
        self.enabled = True

        # Replace "disabled" with usable rule
        if self.current_rule == "disabled":
            self.set_rule(self.get_usable_rule())

    def disable(self):
        '''Sets enabled bool to False (prevents sensor from being checked,
        prevents devices from being turned on).
        '''
        self.enabled = False

    def get_usable_rule(self):
        '''Called when current_rule changes to "enabled" or "disabled" (valid
        as schedule rules but must be immediately replaced for most instances).

        Returns scheduled_rule if valid, otherwise default_rule.

        If neither are valid falls back to "enabled" (only possible for devices
        and sensors that support "enabled", others raise exception in __init__
        if default_rule is "enabled" or "disabled").
        '''
        if str(self.scheduled_rule).lower() not in ["enabled", "disabled"]:
            return self.scheduled_rule
        if str(self.default_rule).lower() not in ["enabled", "disabled"]:
            return self.default_rule
        # Last resort: return "enabled" (device/sensor types taht do not
        # support enabled won't reach this because their default_rule cannot
        # be "enabled" or "disabled")
        return "enabled"

    def set_rule(self, rule, scheduled=False):
        '''Takes new rule, validates, if valid sets as current_rule (and
        scheduled_rule if scheduled arg is True) and calls apply_new_rule.

        Args:
          rule:      The new rule, will be set as current_rule if valid
          scheduled: Optional, if True also sets scheduled_rule if rule valid
        '''

        # Check if rule is valid (may return modified rule, eg cast str to int)
        valid_rule = self.rule_validator(rule)
        if valid_rule is not False:
            self.current_rule = valid_rule
            # If called by next_rule: set scheduled_rule
            if scheduled:
                self.scheduled_rule = valid_rule
            log.info("%s: Rule changed to %s", self.name, self.current_rule)
            self.print(f"Rule changed to {self.current_rule}")

            # Update instance attributes to reflect new rule
            self.apply_new_rule()

            return True

        else:
            log.error("%s: Failed to change rule to %s", self.name, rule)
            self.print(f"Failed to change rule to {rule}")
            return False

    def apply_new_rule(self):
        '''Called by set_rule after successful rule change, updates instance
        attributes to reflect new rule.
        Can be extended in subclasses (example: devices call send method).
        '''

        # Rule just changed to disabled
        if self.current_rule == "disabled":
            self.disable()
        # Rule just changed to enabled, replace with usable rule and enable
        elif self.current_rule == "enabled":
            self.current_rule = self.get_usable_rule()
            # Enable instance unless already enabled (prevent loop)
            if not self.enabled:
                self.enable()
        # Instance was previously disabled, enable now that rule has changed
        elif self.enabled is False:
            self.enable()

    def rule_validator(self, rule):
        '''Base validator for universal rules ("enabled" and "disabled").

        Takes rule, returns rule if valid (may return modified rule, eg cast to
        lowercase), return False if rule is invalid.

        Can be extended to support other rules by replacing the validator
        method (called if rule is neither "enabled" nor "disabled").
        '''
        if str(rule).lower() == "enabled" or str(rule).lower() == "disabled":
            return str(rule).lower()
        else:
            return self.validator(rule)

    def validator(self, rule):
        '''Placeholder method called by rule_validator, intended to be replaced
        by subclasses that support additional rule types.
        '''
        return False

    def next_rule(self):
        '''Called by SoftwareTimer interrupt at each scheduled rule change.
        Calls set_rule with first item in rule_queue (see Config.build_queue).
        '''
        log.debug("%s: Scheduled rule change", self.name)
        self.print("Scheduled rule change")
        self.set_rule(self.rule_queue.pop(0), True)

    def get_attributes(self):
        '''Return JSON-serializable dict containing all current attributes.
        Called by API get_attributes endpoint, more verbose than status.
        '''
        attributes = self.__dict__.copy()

        # Replace group object with group name (JSON-compatibility)
        if self.group:
            attributes["group"] = self.group.name

        return attributes

    def get_status(self):
        '''Return JSON-serializable dict containing status information.
        Called by Config.get_status to build API status endpoint response.
        Contains all attributes displayed on the web frontend.
        '''
        return {
            'nickname': self.nickname,
            'type': self._type,
            'enabled': self.enabled,
            'current_rule': self.current_rule,
            'scheduled_rule': self.scheduled_rule,
            'default_rule': self.default_rule
        }

    def print(self, msg):
        '''Takes string, prints with prepended timestamp and instance name.'''

        print_with_timestamp(f"{self.name}: {msg}")
