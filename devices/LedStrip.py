import time
from machine import Pin, PWM
from DimmableLight import DimmableLight


class LedStrip(DimmableLight):
    '''Driver for PWM-driven MOSFET used to dim an LED strip or other device.
    Sets PWM duty cycle when send method is called.

    Args:
      name:         Unique, sequential config name (device1, device2, etc)
      nickname:     User-configured friendly name shown on frontend
      _type:        Instance type, determines driver class and frontend UI
      enabled:      Initial enable state (True or False)
      default_rule: Fallback rule used when no other valid rules are available
      schedule:     Dict with timestamps/keywords as keys, rules as values
      min_rule:     The minimum supported integer rule, used by rule validator
      max_rule:     The maximum supported integer rule, used by rule validator
      pin:          The ESP32 pin connected to the MOSFET gate pin

    The min_rule and max_rule attributes determine the range of supported int
    rules. This can be used to remove very low duty cycles from the supported
    range if they are too dim or cause flickering. The web frontend scales this
    range to 1-100 for visual consistency.

    Supports universal rules ("enabled" and "disabled"), brightness rules (int
    between 0-1023), and fade rules (syntax: fade/target_rule/duration_seconds).
    The default_rule must be an integer or fade (not universal rule).
    '''

    def __init__(self, name, nickname, _type, default_rule, schedule, min_rule, max_rule, pin):
        super().__init__(name, nickname, _type, True, default_rule, schedule, min_rule, max_rule)

        # TODO - Find optimal PWM freq. Default (5 KHz) causes coil whine in
        # downstairs bathroom at 128 duty cycle. Raising significantly reduces
        # max brightness (exceed MOSFET switching time), may need different power supply?
        self.pwm = PWM(Pin(int(pin)), duty=0)

        # Firmware bug workaround, occasionally instantiates with 512 duty
        # cycle despite duty=0. Immediately calling pwm.duty(0) does nothing,
        # but for some reason calling pwm.duty() with no arg fixes issue. Works
        # whether called in print statement or conditional, tested 100+ times.
        if self.pwm.duty() != 0:
            self.pwm.duty(0)  # pragma: no cover

        # Store current brightness, allows smooth transition when rule changes
        self.bright = 0

        self.log.info("Instantiated, pin=%s", pin)

    def send(self, state=1):
        '''Sets PWM duty cycle to current_rule if argument is True.
        Sets PWM duty cycle to 0 if argument is False.
        Gradually fades to new brightness with 1 second transition.
        '''
        self.log.debug(
            "send method called, rule=%s, state=%s",
            self.current_rule, state
        )

        # Refuse to turn disabled device on, but allow turning off (returning
        # True makes group set device state to True - allows turning off when
        # condition changes, would be skipped if device state already False)
        if not self.enabled and state:
            return True

        if state:
            target = int(self.current_rule)
        else:
            target = 0

        # Exit if current already matches target, prevent division by 0 below
        if self.bright == target:
            return True

        # Fade DOWN
        if self.bright > target:
            # Calculate correct delay for 1 second fade
            steps = self.bright - target
            delay = int(1000000 / steps)

            while self.bright > target:
                self.bright -= 1
                self.pwm.duty(self.bright)
                time.sleep_us(delay)

            self.print(f"Faded down to {target}")

        # Fade UP
        else:
            # Calculate correct delay for 1 second fade
            steps = target - self.bright
            delay = int(1000000 / steps)

            while self.bright < target:
                self.bright += 1
                self.pwm.duty(self.bright)
                time.sleep_us(delay)

            self.print(f"Faded up to {target}")

        return True  # Tell calling function that request succeeded

    def get_attributes(self):
        '''Return JSON-serializable dict containing all current attributes
        Called by API get_attributes endpoint, more verbose than status
        '''
        attributes = super().get_attributes()
        # Remove Pin object (not serializable)
        del attributes["pwm"]
        return attributes
