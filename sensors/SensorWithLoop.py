import asyncio
from Sensor import Sensor


class SensorWithLoop(Sensor):
    '''Base class for all sensor drivers which use a loop to detect when their
    condition is met (instead of pin interrupt). Sensors that output a numeric
    value (such as temperature sensors) must periodically poll the sensor and
    compare the current reading to an on/off threshold (usually current_rule).

    Args:
      name:         Unique, sequential config name (sensor1, sensor2, etc)
      nickname:     User-configured friendly name shown on frontend
      _type:        Instance type, determines driver class and frontend UI
      enabled:      Initial enable state (True or False)
      default_rule: Fallback rule used when no other valid rules are available
      targets:      List of device names (device1 etc) controlled by sensor

    Subclasses must implement an async monitor method containing an infinite
    loop that checks the sensor condition and calls self.refresh_group when the
    condition is met. The loop must await asyncio.sleep at some point to allow
    other tasks to run (use this to set the polling interval, eg 1 second). The
    loop should be wrapped in try/except and exit when asyncio.CancelledError
    is raised.

    The disable method stops the loop to prevent the group from refreshing
    while the sensor is disabled. The enable method recreates the loop.

    Supports universal rules ("enabled" and "disabled"). Additional rules can
    be supported by replacing the validator method in subclass.
    '''

    def __init__(self, name, nickname, _type, enabled, default_rule, targets):
        super().__init__(name, nickname, _type, enabled, default_rule, targets)

        # Stores monitor loop asyncio.Task object (subclass init method should
        # assign this to return value of asyncio.create_task(self.monitor()))
        self.monitor_task = None

    def enable(self):
        '''Sets enabled bool to True (allows sensor to be checked), ensures
        current_rule contains a usable value, refreshes group (check sensor),
        restarts monitor loop if stopped (checks user activity every second).
        '''

        # Restart loop if stopped
        if self.monitor_task is None:
            self.log.debug("%s: start monitor loop", self.name)
            self.monitor_task = asyncio.create_task(self.monitor())
        super().enable()

    def disable(self):
        '''Sets enabled bool to False (prevents sensor from being checked),
        stops monitor loop, and refreshes group (turn devices OFF if other
        sensor conditions not met).
        '''

        # Stop loop if running
        if self.monitor_task is not None:
            self.log.debug("%s: stop monitor loop", self.name)
            self.monitor_task.cancel()
            # Allow enable method to restart loop
            self.monitor_task = None
        super().disable()

    async def monitor(self):
        '''Placeholder method - subclasses must implement method containing an
        infinite loop that checks the sensor condition and calls refresh_group
        when the condition changes.
        '''
        raise NotImplementedError('Must be implemented in subclass')

    def get_attributes(self):
        '''Return JSON-serializable dict containing all current attributes
        Called by API get_attributes endpoint, more verbose than status
        '''
        attributes = super().get_attributes()
        # Replace monitor_task with True or False
        if attributes["monitor_task"] is not None:
            attributes["monitor_task"] = True
        else:
            attributes["monitor_task"] = False
        return attributes
