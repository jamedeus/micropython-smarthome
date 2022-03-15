from machine import Timer
import time



class SoftwareTimer():
    def __init__(self):

        # Real hardware timer
        self.timer = Timer(0)

        # Store expiration time (epoch) as index, callback as value
        self.schedule = {}

        # Sorted first to last, same keys as self.schedule
        self.queue = []

        self.current_run = None
        self.next_callback = None



    # Return epoch time in miliseconds
    def epoch_now(self):
        return (time.mktime(time.localtime()) * 1000)



    # Period in miliseconds
    def create(self, period, callback, name):
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

        self.init_hware()



    # Allow a calling function to cancel all it's existing timers
    def cancel(self, name):
        # Delete any items with same name
        for i in self.schedule:
            if name in self.schedule[i]:
                del self.schedule[i]

        # Rebuild queue
        self.queue = []
        for i in self.schedule:
            self.queue.append(i)

        self.queue.sort()

        # Call init to cancel running timer, start next timer
        self.init_hware()



    def init_hware(self):

        now = self.epoch_now()

        # Stop any running timer
        self.timer.deinit()

        # Only get first valid item (expires in future)
        for i in self.queue:
            if now < i:
                self.current_run = i
                self.next_callback = self.schedule[i][1]
                break
        else:
            # print("No timers in queue")
            return True

        period = int(self.current_run - now)

        self.timer.init(period=period, mode=Timer.ONE_SHOT, callback=self.run)



    def run(self, timer="optional"):
        # Remove the expired entry
        del self.schedule[self.current_run]
        del self.queue[self.queue.index(self.current_run)]

        # Run callback
        self.next_callback()

        # Start next timer
        self.init_hware()



timer = SoftwareTimer()
