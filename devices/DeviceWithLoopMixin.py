import asyncio


class DeviceWithLoopMixin():
    '''A mixin for device drivers which use a loop to update their state in
    response to external changes (user changing brightness from wall dimmer,
    flipping light switch, etc). Extends the enable and disable methods to
    start and stop the loop respectively.
    '''

    def __init__(self, **kwargs):
        # Stores monitor loop asyncio.Task object (subclass init method should
        # assign this to return value of asyncio.create_task(self.monitor()))
        self.monitor_task = None

        super().__init__(**kwargs)

    def enable(self):
        '''Sets enabled bool to True (allows device to be turned on), ensures
        current_rule contains a usable value, and turns the device on if group
        state is True (one or more sensor targeting device has condition met).
        Restarts monitor loop if stopped (poll device for external changes).
        '''

        # Restart loop if stopped
        if self.monitor_task is None:
            self.log.debug("%s: start monitor loop", self.name)
            self.monitor_task = asyncio.create_task(self.monitor())
        super().enable()

    def disable(self):
        '''Sets enabled bool to False (prevents device from being turned on),
        turns device off if currently turned on, and stops monitor loop.
        '''

        # Stop loop if running
        if self.monitor_task is not None:  # pragma: no branch
            self.log.debug("%s: stop monitor loop", self.name)
            self.monitor_task.cancel()
            # Allow enable method to restart loop
            self.monitor_task = None
        super().disable()

    async def monitor(self):
        '''Placeholder method - subclasses must implement method containing an
        infinite loop that checks device state and updates self.current_rule
        and/or self.state in response to external changes.
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
