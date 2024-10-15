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

        # Keys are expiration times (epoch), values are 2-tuples with caller
        # name as first member and callback function as second member.
        self.schedule = {}

        # Keys from self.schedule sorted chronologically, used to determine
        # next due timer
        self.queue = []

        # Stores keys of expired timers after their callback is run, used to
        # remove from self.schedule after running all due timers
        self.delete = []

        # Allows loop to be paused when no timers are expiring soon
        self.pause = False

        # Used to prevent modifying queue while loop is iterating queue
        self.lock = asyncio.Lock()

    def epoch_now(self):
        '''Return current micropython epoch time in milliseconds.'''
        return time.time_ns() // 1000000

    def create(self, period, callback, name):
        '''Takes period (milliseconds), callback function, and name of caller.
        Creates timer to run callback after period expires. If a timer created
        by name already exists it will be canceled to prevent conflicts (except
        scheduler name used for schedule rule callbacks).
        '''
        asyncio.create_task(self._create(period, callback, name))

    async def _create(self, period, callback, name):
        '''Coroutine started by create method, uses lock to avoid conflict.'''

        # Wait for loop to finish iterating queue before modifying, prevent
        # loop from running next iteration until done modifying
        async with self.lock:
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

            self.schedule[expiration] = (name, callback)

            self._rebuild_queue()

            # Resume loop if paused
            self.pause = False

    def cancel(self, name):
        '''Takes caller name, cancels all timers with the same name.'''
        asyncio.create_task(self._cancel(name))

    async def _cancel(self, name):
        '''Coroutine started by cancel method, uses lock to avoid conflict.'''

        # Wait for loop to finish iterating queue before modifying, prevent
        # loop from running next iteration until done modifying
        async with self.lock:
            # Delete any items with same name
            for i in list(self.schedule).copy():
                if name in self.schedule[i]:
                    del self.schedule[i]

            self._rebuild_queue()

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
                # Acquire lock to prevent modifying queue while iterating
                async with self.lock:
                    # Iterate chronological queue until first unexpired timer found
                    for i in self.queue:
                        if self.epoch_now() >= i:
                            # Run expired timer callback, add timestamp to list
                            # of items to be removed from queue
                            self.schedule[i][1]()
                            self.delete.append(i)
                        else:
                            # First unexpired timer found
                            # If not due for >1 second: pause loop, create
                            # interrupt to resume when timer due
                            period = int(i - self.epoch_now())
                            if period > 1000:
                                self.pause = True
                                self.timer.init(
                                    period=period,
                                    mode=Timer.ONE_SHOT,
                                    callback=self._resume
                                )
                            break

                    else:
                        # Pause loop indefinitely if no unexpired timer found
                        # (ran all timers, will unpause when new timer created)
                        self.pause = True
                        self.timer.deinit()

                    # Delete timers that were just run
                    for i in self.delete:
                        del self.schedule[i]
                        del self.queue[self.queue.index(i)]

                    # Clear list for next loop
                    self.delete = []

            else:
                # Wait for hardware interrupt to unpause loop
                await asyncio.sleep_ms(50)


timer = SoftwareTimer()
