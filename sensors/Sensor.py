from micropython import schedule
from Instance import Instance


class Sensor(Instance):
    '''Base class for all sensor drivers, inherits universal API methods and
    attributes from core.Instance and adds sensor-specific functionality

    Args:
      name:         Unique, sequential config name (sensor1, sensor2, etc)
      nickname:     User-configured friendly name shown on frontend
      _type:        Instance type, determines driver class and frontend UI
      enabled:      Initial enable state (True or False)
      default_rule: Fallback rule used when no other valid rules are available
      schedule:     Dict with timestamps/keywords as keys, rules as values
      targets:      List of device names (device1 etc) controlled by sensor

    Subclassed by all sensor drivers. Drivers must implement condition_met
    method (checks sensor and returns True if devices should be turned ON,
    False if devices should be turned OFF, None if no change is needed).

    Supports universal rules ("enabled" and "disabled"). Additional rules can
    be supported by replacing the validator method in subclass.
    '''

    def __init__(self, name, nickname, _type, enabled, default_rule, schedule, targets, **kwargs):
        # List of Device instances controlled by Sensor (Config.build_groups
        # adds sensors with identical targets attribute to same Group instance)
        self.targets = targets

        super().__init__(
            name=name,
            nickname=nickname,
            _type=_type,
            enabled=enabled,
            default_rule=default_rule,
            schedule=schedule,
            **kwargs
        )

    def refresh_group(self):
        '''Calls Group._refresh method to check conditions of all sensors in
        group, update state of all devices in group to match condition.
        '''
        if self.group:
            self.print(f"Refreshing {self.group.name}")
            schedule(self.group._refresh, None)  # pylint: disable=W0212

    def enable(self):
        '''Sets enabled bool to True (allows sensor to be checked), ensures
        current_rule contains a usable value, refreshes group (check sensor).
        '''
        super().enable()

        # Check conditions of all sensors in group
        self.refresh_group()

    def disable(self):
        '''Sets enabled bool to False (prevents sensor from being checked) and
        refreshes group (turn devices OFF if other sensor conditions not met).
        '''
        super().disable()

        # Check conditions of all sensors in group
        self.refresh_group()

    def condition_met(self):
        '''Placeholder method - subclasses must implement method which returns
        True when sensor activated, False when not activated.
        '''
        raise NotImplementedError('Must be implemented in subclass')

    def trigger(self):
        '''Called by trigger_sensor API endpoint, simulates sensor condition
        met. Disabled by default, must be implemented in supported subclasses.
        '''
        return False

    def add_routines(self):
        '''Placeholder function called by Config.build_groups after Sensor is
        added to Group, appends functions to Group's post_action_routines list
        (each called after group refreshes with no errors).
        Must be implemented by subclasses which require post-action routines.
        '''
        return

    def get_attributes(self):
        '''Return JSON-serializable dict containing all current attributes
        Called by API get_attributes endpoint, more verbose than status
        '''
        attributes = super().get_attributes()

        # Replace device instances with instance.name attribute
        attributes["targets"] = []
        for i in self.targets:
            attributes["targets"].append(i.name)

        return attributes

    def get_status(self):
        '''Return JSON-serializable dict containing status information.
        Called by Config.get_status to build API status endpoint response.
        Contains all attributes displayed on the web frontend.
        '''
        status = super().get_status()
        status['condition_met'] = self.condition_met()
        status['targets'] = [t.name for t in self.targets]
        return status
