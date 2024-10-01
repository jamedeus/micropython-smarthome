import time
import asyncio
from machine import Timer


class SoftwareTimer():
    '''Wraps a single ESP32 hardware timer and provides methods to support an
    arbitrary number of virtual timers. The physical hardware timer is used to
    create an interrupt when the next virtual timer is due. This ensures that
    callbacks run when scheduled, unlike asyncio tasks which may not run until
    other tasks yield.
    '''

    def __init__(self):

        # Real hardware timer
        self.timer = Timer(0)

        # Keys are expiration times (epoch), values are lists with caller name
        # as first member and callback function as second member.
        self.schedule = {}

        # Keys from self.schedule sorted chronologically, used to determine
        # next due timer
        self.queue = []

        # Stores keys of expired timers after their callback is run, used to
        # remove from self.schedule after running all due timers
        self.delete = []

        # Allows loop to be paused while rebuilding queue to avoid conflicts
        self.pause = False

    def epoch_now(self):
        '''Return current micropython epoch time in milliseconds.'''
        return time.time() * 1000

    def create(self, period, callback, name):
        '''Takes period (milliseconds), callback function, and name of caller.
        Creates timer to run callback after period expires. If a timer created
        by name already exists it will be canceled to prevent conflicts (except
        scheduler name used for schedule rule callbacks).
        '''

        # Stop loop while adding timer (queue briefly empty)
        self.pause = True

        # Milliseconds until timer due
        expiration = self.epoch_now() + int(period)

        # Prevent overwriting existing item with same expiration time
        if expiration in self.schedule:
            while True:
                # Add 1 ms until expiration is unique
                expiration += 1
                if expiration not in self.schedule:
                    break

        # Callers are only allowed 1 timer each (except schedule rule timers)
        # Delete existing timers with same name before adding
        if not name == "scheduler":
            for i in list(self.schedule).copy():
                if name in self.schedule[i]:
                    del self.schedule[i]

        self.schedule[expiration] = [name, callback]

        self._rebuild_queue()

        # Resume loop
        self.pause = False

    def cancel(self, name):
        '''Takes caller name, cancels all timers with the same name.'''

        # Stop loop while canceling timer (queue briefly empty)
        self.pause = True

        # Delete any items with same name
        for i in list(self.schedule).copy():
            if name in self.schedule[i]:
                del self.schedule[i]

        self._rebuild_queue()

        # Resume loop
        self.pause = False

    def _rebuild_queue(self):
        '''Clears queue, repopulates with keys of self.schedule and sorts
        chronologically. Must be called after self.schedule is modified.
        '''
        self.queue = []
        for i in self.schedule:
            self.queue.append(i)
        self.queue.sort()

    def _resume(self, _=None):
        '''Callback used to unpause loop right before next timer expires'''
        self.pause = False

    async def loop(self):
        '''Coroutine checks for expired timers in queue, runs their callbacks,
        and removes them from the queue. If no timers are due within the next
        second loop pauses and creates interrupt to resume when next timer due.
        '''
        while True:
            if not self.pause:
                # Iterate chronological queue until first unexpired timer found
                for i in self.queue:
                    try:
                        if self.epoch_now() >= i:
                            # Run expired timer callback, add timestamp to list
                            # of items to be removed from queue
                            self.schedule[i][1]()
                            self.delete.append(i)
                        else:
                            # First unexpired timer found, store timestamp
                            next_rule = i
                            break
                    except KeyError:
                        # Prevent crash if timer canceled while loop running
                        pass

                # Delete timers that were just run
                for i in self.delete:
                    try:
                        del self.schedule[i]
                        del self.queue[self.queue.index(i)]
                    except KeyError:
                        # Prevent crash if timer canceled while loop running
                        pass

                # Clear list for next loop
                self.delete = []

                # Get time (milliseconds) until next timer due
                try:
                    period = int(next_rule - self.epoch_now())

                    # Prevent carrying over to next loop when last queued item
                    # runs (results in negative period for wakeup timer)
                    del next_rule
                except NameError:
                    # No timers in queue, sleep for 1 hour (will be interrupted
                    # if timer is added)
                    period = 3600000

                # If next timer >1 second away: pause loop, set hardware timer
                # to unpause when timer due
                if period > 1000:
                    self.pause = True
                    self.timer.init(
                        period=period,
                        mode=Timer.ONE_SHOT,
                        callback=self._resume
                    )

            else:
                # Yield until hardware interrupt unpauses loop
                await asyncio.sleep_ms(50)


timer = SoftwareTimer()
