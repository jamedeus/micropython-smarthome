import threading
import time


class Pin:
    IN = 'IN'
    OUT = 'OUT'
    PULL_DOWN = 'PULL_DOWN'
    IRQ_RISING = None

    def __init__(self, pin, mode=None, pull=None, value=0):
        self.pin = pin
        self.mode = mode
        self.pull = pull
        self.pin_state = value

    def value(self, val=None):
        if val is None:
            return self.pin_state
        else:
            self.pin_state = val

    def irq(self, trigger=None, handler=None):
        pass


class PWM:
    def __init__(self, pin, duty=0):
        self.pin = pin
        self._duty = duty

    def duty(self, value=None):
        if value is not None:
            self._duty = value
        return self._duty


class SoftI2C:
    def __init__(self, scl, sda):
        pass


class Timer:
    ONE_SHOT = 'ONE_SHOT'

    # Store existing timers, return existing if same timer_ID used again
    # Simulate behavior of real Timer class, allows accessing same "hardware
    # timer" from multiple contexts
    _timers = {}

    def __new__(cls, timer_id, *args, **kwargs):
        # If timer_id exists in dict, return existing
        if timer_id in cls._timers:
            return cls._timers[timer_id]

        # If timer_id used for first time: create new timer, add to dict
        timer = super().__new__(cls)
        cls._timers[timer_id] = timer
        timer.stop_event = threading.Event()  # This event is used to stop the thread
        return timer

    def init(self, period, mode=None, callback=None):
        # Convert ms to seconds
        self.period = period / 1000.0
        self.callback = callback

        # Remember start time, used by value()
        self.start_time = time.time()

        # Clear event if previously set by deinit
        if self.stop_event.is_set():
            self.stop_event.clear()

        # Create thread that runs callback after period seconds
        # Daemon prevents test script hanging after complete
        self.thread = threading.Thread(target=self.handler)
        self.thread.daemon = True
        self.thread.start()

    def deinit(self):
        # Set stop event, breaks wait method in handler thread
        self.stop_event.set()
        self.start_time = None

    # Runs in new thread to simulate callback timer
    def handler(self):
        # Wait method can be stopped with stop_event.set()
        stopped = self.stop_event.wait(self.period)
        # Callback runs if stop_event.set() was not called within period
        if not stopped and self.callback is not None:
            self.callback(self)

    def value(self):
        # Return remaining time in ms
        if self.start_time is not None:
            elapsed_time = time.time() - self.start_time
            remaining_time = self.period - elapsed_time
            return max(0, remaining_time) * 1000
        else:
            return 0


class RTC:
    def datetime(self, time_tuple):
        pass


def reset():
    pass
