from machine import Pin, PWM
import logging
import time
from DimmableLight import DimmableLight

# Set name for module's log lines
log = logging.getLogger("LedStrip")


class LedStrip(DimmableLight):
    def __init__(self, name, nickname, _type, default_rule, min_bright, max_bright, pin):
        super().__init__(name, nickname, _type, True, None, default_rule, min_bright, max_bright)

        # TODO - Find optimal PWM freq. Default (5 KHz) causes coil whine in downstairs bathroom at 128 duty cycle.
        # Raising significantly reduces max brightness (exceed MOSFET switching time), may need different power supply?
        self.pwm = PWM(Pin(int(pin)), duty=0)

        # Firmware bug workaround, occasionally instantiates with 512 duty cycle despite duty=0. Immediately calling
        # pwm.duty(0) does nothing, but for some reason calling pwm.duty() with no argument fixes the issue. Works
        # whether called in print statement or conditional, tested 100+ times.
        if self.pwm.duty() != 0:
            self.pwm.duty(0)

        # Store current brightness, allows smooth transition when rule changes
        self.bright = 0

        log.info(f"Instantiated LedStrip named {self.name} on pin {pin}")

    def set_rule(self, rule):
        # Check if rule is valid using subclass method - may return a modified rule (ie cast str to int)
        valid_rule = self.rule_validator(rule)
        if str(valid_rule) == "False":
            log.error(f"{self.name}: Failed to change rule to {rule}")
            print(f"{self.name}: Failed to change rule to {rule}")
            return False

        elif str(valid_rule).startswith("fade"):
            # Parse fade parameters, start fade (see DimmableLight class)
            return self.start_fade(valid_rule)

        else:
            self.current_rule = valid_rule
            print(f"{self.name}: Rule changed to {self.current_rule}")
            log.info(f"{self.name}: Rule changed to {self.current_rule}")

            # If fade in progress when rule changed, abort
            if self.fading:
                self.fading = False

            # Rule just changed to disabled
            if self.current_rule == "disabled":
                self.send(0)
                self.disable()
            # Rule just changed to enabled, replace with usable rule (default) and enable
            elif self.current_rule == "enabled":
                self.current_rule = self.default_rule
                self.enable()
            # Device was previously disabled, enable now that rule has changed
            elif self.enabled is False:
                self.enable()
            # Device is currently on, run send so new rule can take effect
            elif self.state is True:
                self.send(1)

            return True

    def send(self, state=1):
        # Refuse to turn disabled device on, but allow turning off
        if not self.enabled and state:
            # Return True causes group to flip state to True, even though device is off
            # This allows turning off (would be skipped if state already == False)
            return True

        if state:
            target = self.current_rule
        else:
            target = 0

        # Exit if current already matches target, prevent division by 0 below
        if self.bright == target: return True

        # Fade DOWN
        if self.bright > target:
            # Calculate correct delay for 1 second fade
            steps = self.bright - target
            delay = int(1000000 / steps)

            while self.bright > target:
                self.bright -= 1
                self.pwm.duty(self.bright)
                time.sleep_us(delay)

            print(f"{self.name}: Faded down to {target}")

        # Fade UP
        else:
            # Calculate correct delay for 1 second fade
            steps = target - self.bright
            delay = int(1000000 / steps)

            while self.bright < target:
                self.bright += 1
                self.pwm.duty(self.bright)
                time.sleep_us(delay)

            print(f"{self.name}: Faded up to {target}")

        return True  # Tell calling function that request succeeded
