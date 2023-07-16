import threading
import time


class Pin:
    IN = 'IN'
    OUT = 'OUT'
    PULL_DOWN = 'PULL_DOWN'
    IRQ_RISING = None

    def __init__(self, pin, mode=None, pull=None):
        self.pin = pin
        self.mode = mode
        self.pull = pull
        self.pin_state = 0

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
        self.duty = duty

    def duty(self, value=None):
        if value is not None:
            self.duty = value
        return self.duty


class SoftI2C:
    def __init__(self, scl, sda):
        pass


class Timer:
    ONE_SHOT = 'ONE_SHOT'

    def __init__(self, timer_id):
        self.timer_id = timer_id
        self.callback = None
        self.period = None
        self.thread = None

    def init(self, period, mode=None, callback=None):
        # Convert ms to seconds
        self.period = period / 1000.0
        self.callback = callback

        # Create threat that runs callback after period seconds
        self.thread = threading.Thread(target=self.handler)
        self.thread.start()

    # Runs in new thread to simulate callback timer
    def handler(self):
        time.sleep(self.period)
        if self.callback is not None:
            self.callback(self)
