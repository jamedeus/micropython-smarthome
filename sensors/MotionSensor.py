import logging
from math import isnan
from machine import Pin
import SoftwareTimer
from Sensor import Sensor

# Set name for module's log lines
log = logging.getLogger("MotionSensor")


class MotionSensor(Sensor):
    def __init__(self, name, nickname, _type, default_rule, targets, pin):
        super().__init__(name, nickname, _type, True, None, default_rule, targets)

        # Prevent instantiating with invalid default_rule
        if str(self.default_rule).lower() in ("enabled", "disabled"):
            log.critical(f"{self.name}: Received invalid default_rule: {self.default_rule}")
            raise AttributeError

        # Pin setup
        self.sensor = Pin(int(pin), Pin.IN, Pin.PULL_DOWN)

        # Create hardware interrupt
        self.enable()

        log.info(f"Instantiated MotionSensor (type={self._type}) named {self.name} on pin {pin}")

    def enable(self):
        self.motion = False

        super().enable()

        # Create hardware interrupt (both rising and falling)
        self.sensor.irq(trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING, handler=self.pin_interrupt)

    def disable(self):
        super().disable()

        # Disable hardware interrupt
        self.sensor.irq(handler=None)

        # Stop any reset timer that may be running
        SoftwareTimer.timer.cancel(self.name)

    def condition_met(self):
        return self.motion

    def apply_new_rule(self):
        super().apply_new_rule()

        # If reset timer currently running, replace so new rule takes effect
        if self.motion:
            self.start_reset_timer()

    def validator(self, rule):
        try:
            if rule is None:
                return 0
            # Prevent incorrectly accepting True and False (last condition
            # casts to 1.0, 0.0 respectively)
            elif isinstance(rule, bool):
                return False
            # Prevent accepting NaN (is valid float but breaks arithmetic)
            elif isnan(float(rule)):
                return False
            else:
                return float(rule)
        except (ValueError, TypeError):
            return False

    # Takes positive or negative float, adds to self.current_rule
    def increment_rule(self, amount):
        # Throw error if arg is not int or float
        try:
            amount = float(amount)
            if isnan(amount):
                raise ValueError
        except (ValueError, TypeError):
            return {"ERROR": f"Invalid argument {amount}"}

        # Add amount to current rule
        try:
            new = float(self.current_rule) + amount
        except (ValueError, TypeError):
            return {"ERROR": f"Unable to increment current rule ({self.current_rule})"}

        return self.set_rule(new)

    # Interrupt routine, called when pin value changes (rising or falling)
    def pin_interrupt(self, pin=""):
        # Turn targets on and start reset timer if motion detected
        if self.sensor.value():
            self.motion_detected()

        # Turn off targets if motion not detected and reset timer is disabled
        # (otherwise leave targets on until reset timer expires)
        elif self.current_rule == 0:
            self.motion = False
            self.refresh_group()

    # Called when sensor is activated (pin HIGH or trigger called)
    def motion_detected(self):
        # Set motion attribute if not already set
        if not self.motion:
            self.motion = True
            self.print("Motion detected")
            log.debug(f"{self.name}: Motion detected")

        # Start reset timer (or restart if sensor retriggered)
        self.start_reset_timer()

        # Check conditions of all sensors in group
        self.refresh_group()

    # Called when motion is detected or rule changes, starts timer to reset
    # motion attribute and refresh group in <current_rule> minutes
    def start_reset_timer(self):
        # Set reset timer unless current rule is 0 (no reset timer) or sensor is disabled
        if not (self.current_rule == 0 or self.current_rule == "disabled"):
            try:
                # Convert delay (minutes) to milliseconds, start timer
                off = float(self.current_rule) * 60000
                SoftwareTimer.timer.create(off, self.reset_timer, self.name)
            except (ValueError, TypeError):
                self.print(f"Failed to start reset timer, current_rule = {self.current_rule}")
                log.debug(f"{self.name}: Failed to start reset timer, current_rule = {self.current_rule}")
        else:
            # Stop reset timer (may be running from before delay set to None)
            SoftwareTimer.timer.cancel(self.name)

    # Called when reset timer expires
    def reset_timer(self, timer=None):
        log.info(f"{self.name}: reset_timer interrupt")

        # Only reset if sensor not detecting motion
        if not self.sensor.value():
            # Reset motion, causes main loop to fade lights off
            self.motion = False

            # Check conditions of all sensors in group
            self.refresh_group()

        # Restart timer if still detecting motion (prevents getting stuck ON if
        # motion continuously detected for whole timer duration - if it stopped
        # detecting and restarted the timer would have been reset before this).
        else:
            self.start_reset_timer()

    # Allow API commands to simulate the sensor being triggered
    def trigger(self):
        self.motion_detected()
        return True
