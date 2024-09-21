from Instance import Instance


class Device(Instance):
    '''Base class for all device drivers, inherits universal API methods and
    attributes from core.Instance and adds device-specific functionality

    Args:
      name:         Unique, sequential config name (device1, device2, etc)
      nickname:     User-configured friendly name shown on frontend
      _type:        Instance type, determines driver class and frontend UI
      enabled:      Initial enable state (True or False)
      default_rule: Fallback rule used when no other valid rules are available

    Subclassed by all device drivers. Drivers must implement send method (takes
    bool argument, turns device ON if True, turns device OFF if False).

    Supports universal rules ("enabled" and "disabled"). Additional rules can
    be supported by replacing the validator method in subclass.
    '''

    def __init__(self, name, nickname, _type, enabled, default_rule):
        super().__init__(name, nickname, _type, enabled, default_rule)

        # Record device's on/off state, prevent turning on/off when already on/off
        # Included in status object, used by API to display device state
        self.state = None

        # List of Sensor instances which control the device, populated by Config
        # when sensors are instantiated
        self.triggered_by = []

    def enable(self):
        '''Sets enabled bool to True (allows device to be turned on), ensures
        current_rule contains a usable value, and turns the device on if group
        state is True (one or more sensor targeting device has condition met).
        '''

        super().enable()

        # If other devices in group are on, turn on to match state
        try:
            if self.group.state is True:
                self.log.debug("group state is True, turning on")
                success = self.send(1)
                if success:
                    self.state = True
                else:
                    # Force group to turn on again, retrying until successful
                    # (recover from failed send command above)
                    #
                    # Only used after failed send due to side effects - if user
                    # turned another device in group OFF while this device was
                    # disabled, then re-enabled this device, group will turn
                    # BOTH on (but user only wanted to turn this one on).
                    self.group.state = False
        except AttributeError:
            pass

    def disable(self):
        '''Sets enabled bool to False (prevents device from being turned on)
        and turns device off if currently turned on.
        '''

        # Turn off before disabling
        if self.state:
            self.log.debug("turning off")
            self.send(0)
            self.state = False
        super().disable()

    def send(self, _):
        '''Placeholder method - subclasses must implement method which turns
        device on when argument is True, turns off when argument is False
        '''
        raise NotImplementedError('Must be implemented in subclass')

    def apply_new_rule(self):
        '''Called by set_rule after successful rule change, updates instance
        attributes to reflect new rule. If device currently turned on calls
        send method so new rule can take effect.
        '''
        super().apply_new_rule()

        # Device is currently on, run send so new rule can take effect
        if self.state is True:
            self.send(1)

    def get_attributes(self):
        '''Return JSON-serializable dict containing all current attributes
        Called by API get_attributes endpoint, more verbose than status
        '''
        attributes = super().get_attributes()

        # Replace sensor instances with instance.name attributes
        attributes["triggered_by"] = []
        for i in self.triggered_by:
            attributes["triggered_by"].append(i.name)

        return attributes

    def get_status(self):
        '''Return JSON-serializable dict containing status information.
        Called by Config.get_status to build API status endpoint response.
        Contains all attributes displayed on the web frontend.
        '''
        status = super().get_status()
        status['turned_on'] = self.state
        return status
