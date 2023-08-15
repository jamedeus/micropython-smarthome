import logging
from Instance import Instance

# Set name for module's log lines
log = logging.getLogger("Device")


class Device(Instance):
    def __init__(self, name, nickname, _type, enabled, current_rule, default_rule):
        super().__init__(name, nickname, _type, enabled, current_rule, default_rule)

        # Record device's on/off state
        self.state = None

        # Will be populated with instances of all triggering sensors later
        self.triggered_by = []

    def enable(self):
        super().enable()

        # If other devices in group are on, turn on to match state
        try:
            if self.group.state is True:
                success = self.send(1)
                if success:
                    self.state = True
                else:
                    # Force group to turn on again, retrying until successful (recover from failed send command above)
                    # Used as last resort due to side effects - if user previously turned OFF another device in group,
                    # then re-enables this device, group will turn BOTH on (but user only wanted to turn this one on)
                    self.group.state = False
        except AttributeError:
            pass

    def disable(self):
        # Turn off before disabling
        if self.state:
            self.send(0)
            self.state = False

        self.enabled = False

    # Called by set_rule after current_rule changed
    # Updates instance attributes to reflect new rule
    # Enable/disable, prevent unusable rules, call send method so new rule takes effect
    def apply_new_rule(self):
        # Rule just changed to disabled, turn off and disable
        if self.current_rule == "disabled":
            self.send(0)
            self.disable()
        # Rule just changed to enabled, replace with usable rule (default) and enable
        elif self.current_rule == "enabled":
            self.current_rule = self.default_rule
            self.enable()
        # Device was previously disabled, enable now that rule has changed
        elif self.enabled is False:
            self.enable()
        # Device is currently on, run send so new rule can take effect
        elif self.state is True:
            self.send(1)

    # Return JSON-serializable dict containing all current attributes
    # Called by API get_attributes endpoint
    def get_attributes(self):
        attributes = super().get_attributes()

        for i in self.__dict__:
            # Remove object references
            if i in ("pwm", "mosfet", "relay"):
                del attributes[i]

        # Replace sensor instances with instance.name attributes
        attributes["triggered_by"] = []
        for i in self.triggered_by:
            attributes["triggered_by"].append(i.name)

        return attributes
