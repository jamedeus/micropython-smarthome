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

    def __init__(self, timer_id):
        self.timer_id = timer_id
        self.callback = None
        self.period = None
        self.start_time = None
        self.thread = None
        self.stop_event = threading.Event()

    def init(self, period, mode=None, callback=None):
        # Convert ms to seconds
        self.period = period / 1000.0
        self.callback = callback

        # Remember start time, used by value()
        self.start_time = time.time()

        # Create thread that runs callback after period seconds
        self.thread = threading.Thread(target=self.handler)
        self.thread.start()

    def deinit(self):
        self.stop_event.set()
        if self.thread is not None:
            self.thread.join()
        self.start_time = None

    # Runs in new thread to simulate callback timer
    def handler(self):
        stopped = self.stop_event.wait(self.period)
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
