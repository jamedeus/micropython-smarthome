import asyncio


class DriverLoopMixin():
    '''A mixin-like class used by device and sensor drivers which use a loop to
    periodically poll for changes and update their state (sensors that activate
    at a numeric threshold instead of with an interrupt, devices that need to
    keep their state in sync with an external hardware device, etc).

    Classes using this must have:
    - An async method `monitor` with an infinite loop that terminates if
      asyncio.CancelledError is raised.
    - A `self.monitor_task` attribute which contains the asyncio task for
      self.monitor while it is running and None while it is not running.

    Extends the enable method to start the loop if it is not running and save
    the asyncio task in self.monitor_task.

    Extends the disable method to stop the loop and replace self.monitor_task
    with None.

    Extends the get_attributes method to remove the asyncio task (not JSON
    serializable) from the dict before returning.

    This is NOT a true mixin due to micropython's multiple inheritance
    limitations. Rather than inheritting from the class subclasses must
    override the methods above using this syntax:

        def enable(self):
            return LoopMixin.enable(self)

    See here for details:
    http://docs.micropython.org/en/v1.23.0/micropython-docs.pdf#subsection.3.8.8
    '''

    def enable(self, base_class):
        '''Restarts monitor loop if stopped before calling upstream enable'''

        # Restart loop if stopped
        if self.monitor_task is None:
            self.log.debug("%s: start monitor loop", self.name)
            self.monitor_task = asyncio.create_task(self.monitor())
        base_class.enable(self)

    def disable(self, base_class):
        '''Stops monitor loop if running before calling upstream disable'''

        # Stop loop if running
        if self.monitor_task is not None:  # pragma: no branch
            self.log.debug("%s: stop monitor loop", self.name)
            self.monitor_task.cancel()
            # Allow enable method to restart loop
            self.monitor_task = None
        base_class.disable(self)

    def get_attributes(self, base_class):
        '''Calls upstream get_attributes, replaces the monitor_task attribute
        (asyncio task, non-serializable) with True if the loop is running or
        False if the loop is not running, returns updated dict.
        '''
        attributes = base_class.get_attributes(self)
        # Replace monitor_task with True or False
        if attributes["monitor_task"] is not None:
            attributes["monitor_task"] = True
        else:
            attributes["monitor_task"] = False
        return attributes
