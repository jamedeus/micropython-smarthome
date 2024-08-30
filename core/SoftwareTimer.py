import time
import asyncio
from machine import Timer


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

        # Wakes up loop when new rule added
        # Prevents issue where loop has already determined time until next rule when create is called. Create
        # blocks loop mid-run, adds new rule expiring even sooner, then unblocks. Loop sleeps for the previously
        # determined period, causing new rule to run late.
        self.new_rule_added = False

    # Return epoch time in milliseconds
    def epoch_now(self):
        return (time.mktime(time.localtime()) * 1000)

    # Period in milliseconds
    def create(self, period, callback, name):
        # Stop loop while adding timer (queue briefly empty)
        self.pause = True

        now = self.epoch_now()

        # In milliseconds
        expiration = now + int(period)

        # Prevent overwriting existing item with same expiration time
        if expiration in self.schedule:
            while True:
                expiration += 1  # Add 1 ms until expiration is unique
                if expiration not in self.schedule:
                    break

        # Callers are only allowed 1 timer each - delete existing timers with same name before adding
        # Exempt callers: scheduler, API
        if not name == "scheduler" and not name == "API":
            for i in list(self.schedule).copy():
                if name in self.schedule[i]:
                    del self.schedule[i]

        self.schedule[expiration] = [name, callback]

        self.queue = []
        for i in self.schedule:
            self.queue.append(i)

        self.queue.sort()

        # Resume loop
        self.pause = False # TODO redundant, next line causes it to resume and flips pause - might be causing unpredictable execution flow (ie causes loop to run, loop then pauses, else condition sees new rule and unpauses only to immediately determine it doesn't expire soon (again) and pauses again.)
        self.new_rule_added = True

    # Allow a calling function to cancel all it's existing timers
    def cancel(self, name):
        # Stop loop while canceling timer (queue briefly empty)
        self.pause = True

        # Delete any items with same name
        for i in list(self.schedule).copy():
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
                    try:
                        # Run actions for all expired rules, add to list to be removed from queue
                        if self.epoch_now() >= i:
                            self.schedule[i][1]()  # Run action
                            self.delete.append(i)
                        else:
                            # First unexpired rule found
                            next_rule = i
                            break
                    except KeyError:
                        pass  # Prevent crash if rule was removed by self.cancel while loop running

                # Delete rules that were just run
                for i in self.delete:
                    try:
                        del self.schedule[i]
                        del self.queue[self.queue.index(i)]
                    except KeyError:
                        pass  # Prevent crash if rule was removed by self.cancel while loop running

                self.delete = []

                # Get time until next rule due
                try:
                    period = int(next_rule - self.epoch_now())

                    # Prevent carrying over to next loop after running last queue item, resulting in negative period
                    del next_rule
                except NameError:
                    # No tasks in queue - sleep for 1 hour (will be interrupted if task is added)
                    period = 3600000

                # If next rule >1 seconds away: pause loop, set hardware timer to unpause when rule due
                if period > 1000:
                    self.pause = True
                    self.timer.init(period=period, mode=Timer.ONE_SHOT, callback=self.resume)

            else:
                if self.new_rule_added is True:
                    # Unpause immediately if a new rule was added
                    self.pause = False
                    self.new_rule_added = False
                else:
                    # Wait for timer to unpause loop
                    await asyncio.sleep_ms(50)


timer = SoftwareTimer()
