from machine import Timer
import time
import uasyncio as asyncio



class SoftwareTimer():
    def __init__(self):

        # Real hardware timer
        self.timer = Timer(0)

        # Store expiration time (epoch) as index, callback as value
        self.schedule = {}

        # Sorted first to last, same keys as self.schedule
        self.queue = []

        # Stores expired timers so they can be removed from schedule after iterating
        self.delete = []

        # Allows loop to be paused while rebuilding queue to avoid conflicts
        self.pause = False

        # Start loop
        asyncio.create_task(self.loop())



    # Return epoch time in miliseconds
    def epoch_now(self):
        return (time.mktime(time.localtime()) * 1000)



    # Period in miliseconds
    def create(self, period, callback, name):
        # Stop loop while adding timer (queue briefly empty)
        self.pause = True

        now = self.epoch_now()

        # In miliseconds
        expiration = now + int(period)

        # Prevent overwriting existing item with same expiration time
        if expiration in self.schedule:
            while True:
                expiration += 1 # Add 1 ms until expiration is unique
                if not expiration in self.schedule:
                    break

        # Callers are only allowed 1 timer each (scheduler is exempt) - delete any existing timers with same name before adding
        if not name == "scheduler":
            for i in self.schedule:
                if name in self.schedule[i]:
                    del self.schedule[i]

        self.schedule[expiration] = [name, callback]

        self.queue = []
        for i in self.schedule:
            self.queue.append(i)

        self.queue.sort()

        # Resume loop
        self.pause = False



    # Allow a calling function to cancel all it's existing timers
    def cancel(self, name):
        # Stop loop while canceling timer (queue briefly empty)
        self.pause = True

        # Delete any items with same name
        for i in self.schedule:
            if name in self.schedule[i]:
                del self.schedule[i]

        # Rebuild queue
        self.queue = []
        for i in self.schedule:
            self.queue.append(i)

        self.queue.sort()

        # Resume loop
        self.pause = False



    def resume(self, timer):
        self.pause = False



    async def loop(self):
        while True:
            if not self.pause:

                for i in self.queue:
                    # Run actions for all expired rules, add to list to be removed from queue
                    if self.epoch_now() >= i:
                        self.schedule[i][1]() # Run action
                        self.delete.append(i)

                    else:
                        # First unexpired rule found
                        next_rule = i
                        break

                # Delete rules that were just run
                for i in self.delete:
                    del self.schedule[i]
                    del self.queue[self.queue.index(i)]

                self.delete = []

                # Get time until next rule due
                period = int(next_rule - self.epoch_now())

                # If next rule >5 seconds away: pause loop, set hardware timer to unpause when rule due
                if period > 5000:
                    self.pause = True
                    self.timer.init(period=period, mode=Timer.ONE_SHOT, callback=self.resume)

                # If next rule 5> seconds away: calculate ticks until due, wait until due, run action
                else:
                    deadline = time.ticks_add(time.ticks_ms(), period)
                    while time.ticks_diff(deadline, time.ticks_ms()) > 0:
                        await asyncio.sleep_ms(1)

                    # Run action, remove from queue
                    self.schedule[next_rule][1]()
                    del self.schedule[next_rule]
                    del self.queue[self.queue.index(next_rule)]

            else:
                # Wait for timer to unpause loop
                await asyncio.sleep_ms(50)



timer = SoftwareTimer()
