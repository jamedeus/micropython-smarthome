from machine import Pin
import logging
from Sensor import Sensor
import SoftwareTimer

# Set name for module's log lines
log = logging.getLogger("MotionSensor")


class MotionSensor(Sensor):
    def __init__(self, name, nickname, _type, default_rule, targets, pin):
        super().__init__(name, nickname, _type, True, None, default_rule, targets)

        # Pin setup
        self.sensor = Pin(int(pin), Pin.IN, Pin.PULL_DOWN)

        # Create hardware interrupt
        self.enable()

        log.info(f"Instantiated MotionSensor named {self.name} on pin {pin}")

    def enable(self):
        super().enable()

        self.motion = False

        # Create hardware interrupt
        self.sensor.irq(trigger=Pin.IRQ_RISING, handler=self.motion_detected)

    def disable(self):
        super().disable()

        # Disable hardware interrupt
        self.sensor.irq(handler=None)

        # Stop any reset timer that may be running
        SoftwareTimer.timer.cancel(self.name)

    def condition_met(self):
        return self.motion

    def validator(self, rule):
        try:
            if rule is None:
                return 0
            # Prevent incorrectly accepting True and False (next condition casts to 1.0, 0.0 respectively)
            elif isinstance(rule, bool):
                return False
            else:
                return float(rule)
        except (ValueError, TypeError):
            return False

    def next_rule(self):
        super().next_rule()

        # If reset timer currently running, replace so new rule takes effect
        if self.motion:
            try:
                off = float(self.current_rule) * 60000
                if off > 0:
                    SoftwareTimer.timer.create(off, self.resetTimer, self.name)
            except ValueError:
                pass  # Prevent crash when rule changes to "disabled"

    # Interrupt routine, called when motion sensor triggered
    def motion_detected(self, pin=""):
        if not self.motion:
            print(f"{self.name}: Motion detected")
            log.debug(f"{self.name}: Motion detected")

        self.motion = True

        # Set reset timer unless current rule is 0 (no reset timer) or sensor is disabled
        if not (self.current_rule == 0 or self.current_rule == "disabled"):
            try:
                off = float(self.current_rule) * 60000
                SoftwareTimer.timer.create(off, self.resetTimer, self.name)
            except:
                print(f"CAUGHT: name = {self.name}, rule = {self.current_rule}")

        else:
            # Stop any reset timer that may be running from before delay = None
            SoftwareTimer.timer.cancel(self.name)

    def resetTimer(self, timer="optional"):
        log.info(f"{self.name}: resetTimer interrupt")
        # Reset motion, causes main loop to fade lights off
        self.motion = False
