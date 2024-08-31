import logging
from Instance import Instance

# Set name for module's log lines
log = logging.getLogger("Device")


class Device(Instance):
    def __init__(self, name, nickname, _type, enabled, current_rule, default_rule):
        super().__init__(name, nickname, _type, enabled, current_rule, default_rule)

        # Record device's on/off state, prevent turning on/off when already on/off
        # Included in status object, used by API to display device state
        self.state = None

        # List of Sensor instances which control the device, populated by Config
        # when sensors are instantiated
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
        super().disable()

    # Called by set_rule after current_rule changed
    def apply_new_rule(self):
        super().apply_new_rule()

        # Device is currently on, run send so new rule can take effect
        if self.state is True:
            self.send(1)

    # Return JSON-serializable dict containing all current attributes
    # Called by API get_attributes endpoint, more verbose than status
    def get_attributes(self):
        attributes = super().get_attributes()

        # Replace sensor instances with instance.name attributes
        attributes["triggered_by"] = []
        for i in self.triggered_by:
            attributes["triggered_by"].append(i.name)

        return attributes

    # Return JSON-serializable dict containing state information
    # Called by Config.get_status to build API status response
    def get_status(self):
        status = super().get_status()
        status['turned_on'] = self.state
        return status
