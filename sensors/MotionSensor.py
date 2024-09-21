from math import isnan
from machine import Pin
import SoftwareTimer
from Sensor import Sensor


class MotionSensor(Sensor):
    '''Driver for motion sensors (passive infrared, millimeter wave radar, etc).
    Turns target devices on when sensor detects motion, turns devices off when
    reset timer expires. Reset timer duration is determined by current_rule.
    The reset timer starts over each time motion is detected.

    Args:
      name:         Unique, sequential config name (sensor1, sensor2, etc)
      nickname:     User-configured friendly name shown on frontend
      _type:        Instance type, determines driver class and frontend UI
      enabled:      Initial enable state (True or False)
      default_rule: Fallback rule used when no other valid rules are available
      targets:      List of device names (device1 etc) controlled by sensor
      pin:          The ESP32 pin connected to the sensor output pin

    Supports universal rules ("enabled" and "disabled") and reset timer
    duration (float, number of minutes before sensor resets). Setting the rule
    to 0 disables the reset timer (devices will turn off immediately when the
    sensor no longer detects motion).
    The default_rule must be an integer or float (not universal rule).
    '''

    def __init__(self, name, nickname, _type, default_rule, targets, pin):
        super().__init__(name, nickname, _type, True, default_rule, targets)

        # Prevent instantiating with invalid default_rule
        if str(self.default_rule).lower() in ("enabled", "disabled"):
            self.log.critical(
                "Received invalid default_rule: %s",
                self.default_rule
            )
            raise AttributeError

        # Pin setup
        self.sensor = Pin(int(pin), Pin.IN, Pin.PULL_DOWN)

        # Motion detection state from last hardware interrupt
        self.motion = False

        # Create hardware interrupt
        self.enable()

        self.log.info("Instantiated, pin=%s", pin)

    def enable(self):
        '''Sets enabled bool to True (allows sensor to be checked), ensures
        current_rule contains a usable value, refreshes group (check sensor),
        creates hardware interrupt on motion sensor output pin.
        '''
        self.motion = False

        super().enable()

        # Create hardware interrupt (both rising and falling)
        self.log.debug("create hardware interrupt")
        self.sensor.irq(trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING, handler=self.pin_interrupt)

    def disable(self):
        '''Sets enabled bool to False (prevents sensor from being checked),
        removes sensor pin interrupt, stops reset timer if running, and
        refreshes group (turn devices OFF if other sensor conditions not met).
        '''

        # Disable hardware interrupt, ensure reset timer not running
        self.log.debug("remove hardware interrupt")
        self.sensor.irq(handler=None)
        SoftwareTimer.timer.cancel(self.name)

        super().disable()

    def condition_met(self):
        '''Returns True if sensor detected motion and reset timer has not yet
        expired, returns False if sensor does not detect motion.'''
        return self.motion

    def apply_new_rule(self):
        '''Called by set_rule after successful rule change, updates instance
        attributes to reflect new rule. If reset timer is running restarts so
        new rule can take effect.
        '''
        super().apply_new_rule()

        # If reset timer currently running, replace so new rule takes effect
        if self.motion:
            self.start_reset_timer()

    def validator(self, rule):
        '''Accepts any valid integer or float except NaN.'''

        try:
            # Prevent incorrectly accepting True and False (last condition
            # casts to 1.0, 0.0 respectively)
            if isinstance(rule, bool):
                return False
            # Prevent accepting NaN (is valid float but breaks arithmetic)
            if isnan(float(rule)):
                return False
            # Rule valid if able to cast to float
            return float(rule)
        except (ValueError, TypeError):
            return False

    def increment_rule(self, amount):
        '''Takes positive or negative float, adds to current_rule and calls
        set_rule method. Throws error if current_rule is not an int or float.
        '''

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

    def pin_interrupt(self, _=None):
        '''Interrupt handler called when sensor pin value changes (rising or
        falling) while sensor is enabled. Turns target devices on when rising
        interrupt occurs (motion detected). Turns devices off when falling
        interrupt occurs and reset timer is disabled, otherwise ignores falling
        interrupt (wait for reset timer to turn devices off).
        '''

        # Turn targets on and start reset timer if motion detected
        if self.sensor.value():
            self.log.debug("Motion detected")
            self.motion_detected()

        # Turn off targets if motion not detected and reset timer is disabled
        # (otherwise leave targets on until reset timer expires)
        elif self.current_rule == 0:
            self.log.debug("Motion no longer detected")
            self.motion = False
            self.refresh_group()

    def motion_detected(self):
        '''Called when sensor is activated (pin HIGH interrupt or trigger
        method called). Sets self.motion attribute, turns on target devices,
        and starts reset timer.
        '''

        # Set motion attribute if not already set
        if not self.motion:
            self.motion = True
            self.print("Motion detected")

        # Start reset timer (or restart if sensor retriggered)
        self.start_reset_timer()

        # Check conditions of all sensors in group
        self.refresh_group()

    def start_reset_timer(self):
        '''Starts timer to reset motion attribute and refresh group (turn off
        target devices) in <current_rule> minutes. Called when motion detected
        or current_rule changes.
        '''
        self.log.debug(
            "starting reset timer, current_rule=%s",
            self.current_rule
        )

        # Set reset timer unless disabled or current rule is 0 (no reset timer)
        if self.current_rule not in [0, "disabled"]:
            try:
                # Convert delay (minutes) to milliseconds, start timer
                off = float(self.current_rule) * 60000
                SoftwareTimer.timer.create(off, self.reset_timer, self.name)
            except (ValueError, TypeError):
                self.print(f"Failed to start reset timer, current_rule={self.current_rule}")
                self.log.error(
                    "Failed to start reset timer, current_rule=%s",
                    self.current_rule
                )
        else:
            # Stop reset timer (may be running from before delay set to 0)
            SoftwareTimer.timer.cancel(self.name)

    def reset_timer(self, _=None):
        '''Called when reset timer expires, resets motion attribute and turns
        off target devices.
        '''
        self.log.debug("reset_timer interrupt")

        # Only reset if sensor not detecting motion
        if not self.sensor.value():
            # Reset motion, causes main loop to fade lights off
            self.log.debug("motion no longer detected")
            self.motion = False

            # Check conditions of all sensors in group
            self.refresh_group()

        # Restart timer if still detecting motion (prevents getting stuck ON if
        # motion continuously detected for whole timer duration - if it stopped
        # detecting and restarted the timer would have been reset before this).
        else:
            self.log.debug("motion still detected")
            self.start_reset_timer()

    def trigger(self):
        '''Called by trigger_sensor API endpoint, simulates sensor detecting
        motion (sets motion attribute to True, starts reset timer).
        '''
        self.log.debug("trigger method called")
        self.motion_detected()
        return True

    def get_attributes(self):
        '''Return JSON-serializable dict containing all current attributes
        Called by API get_attributes endpoint, more verbose than status
        '''
        attributes = super().get_attributes()
        # Remove Pin object (not serializable)
        del attributes["sensor"]
        return attributes
