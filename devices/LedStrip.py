from machine import Pin, PWM
import logging
import time
from Device import Device
import SoftwareTimer

# Set name for module's log lines
log = logging.getLogger("LedStrip")


class LedStrip(Device):
    def __init__(self, name, nickname, _type, default_rule, pin, min_bright, max_bright):
        super().__init__(name, nickname, _type, True, None, default_rule)

        # TODO - Find optimal PWM freq. Default (5 KHz) causes coil whine in downstairs bathroom at 128 duty cycle.
        # Raising significantly reduces max brightness (exceed MOSFET switching time), may need different power supply?
        self.pwm = PWM(Pin(pin), duty=0)

        # Firmware bug workaround, occasionally instantiates with 512 duty cycle despite duty=0. Immediately calling
        # pwm.duty(0) does nothing, but for some reason calling pwm.duty() with no argument fixes the issue. Works
        # whether called in print statement or conditional, tested 100+ times.
        if self.pwm.duty() != 0:
            self.pwm.duty(0)

        # Store current brightness, allows smooth transition when rule changes
        self.bright = 0

        self.min_bright = int(min_bright)
        self.max_bright = int(max_bright)

        # Stores parameters in dict when fade in progress
        self.fading = False

        log.info(f"Instantiated LedStrip named {self.name} on pin {pin}")

    def set_rule(self, rule):
        # Check if rule is valid using subclass method - may return a modified rule (ie cast str to int)
        valid_rule = self.rule_validator(rule)
        if str(valid_rule) == "False":
            log.error(f"{self.name}: Failed to change rule to {rule}")
            print(f"{self.name}: Failed to change rule to {rule}")
            return False

        elif str(valid_rule).startswith("fade"):
            # Parse parameters from rule
            cmd, target, period = valid_rule.split("/")

            # If first rule on boot is fade, set target as current_rule (animation probably overdue)
            if self.current_rule is None:
                self.current_rule = int(target)
                print(f"{self.name}: Rule changed to {self.current_rule}")
                log.info(f"{self.name}: Rule changed to {self.current_rule}")
                return True

            # If rule changes to fade after boot, start fade and return first step as current_rule
            print(f"{self.name}: fading to {target} in {period} seconds")
            log.info(f"{self.name}: fading to {target} in {period} seconds")

            if not self.current_rule == "disabled":
                # Get current brightness
                brightness = int(self.current_rule)
            else:
                # Default to 0 if device disabled when fade starts
                brightness = 0

            if int(target) == brightness:
                print("Already at target brightness, skipping fade")
                log.info("Already at target brightness, skipping fade")
                return True

            # Find fade direction, get number of steps, period between steps
            if int(target) > brightness:
                steps = int(target) - brightness
                fade_period = int(period) / steps * 1000

            elif int(target) < brightness:
                steps = brightness - int(target)
                fade_period = int(period) / steps * 1000

            # Ensure device is enabled
            self.enabled = True

            # Create fade timer
            SoftwareTimer.timer.create(fade_period, self.fade, self.name + "_fade")

            # Store fade parameters in dict, used by fade method below
            self.fading = {
                "started": SoftwareTimer.timer.epoch_now(),
                "starting_brightness": brightness,
                "target": int(
                    target
                ),
                "period": fade_period
            }

            # Return starting point (will be set as current rule by device.set_rule)
            return True

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

    def validator(self, rule):
        try:
            if str(rule).startswith("fade"):
                # Parse parameters from rule
                cmd, target, period = rule.split("/")

                if int(period) < 0:
                    return False

                if self.min_bright <= int(target) <= self.max_bright:
                    return rule
                else:
                    return False

            elif isinstance(rule, bool):
                return False

            elif self.min_bright <= int(rule) <= self.max_bright:
                return int(rule)

            else:
                return False

        except (ValueError, TypeError):
            return False

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

    # Called by SoftwareTimer during fade animation, initialized in rule_validator above
    def fade(self):

        # Abort if disabled mid-fade, or if called after fade complete
        if not self.enabled or not self.fading:
            return True

        # Fade to next step (unless fade already complete)
        if not self.fading["target"] == int(self.current_rule):

            # Use starting time, current time, period (time per step) to determine how many steps should have been taken
            steps = (SoftwareTimer.timer.epoch_now() - self.fading["started"]) // self.fading["period"]

            if self.fading["target"] > int(self.current_rule):
                new_rule = self.fading["starting_brightness"] + steps
                if new_rule > self.fading["target"]:
                    new_rule = self.fading["target"]

            elif self.fading["target"] < int(self.current_rule):
                new_rule = self.fading["starting_brightness"] + steps * -1
                if new_rule < self.fading["target"]:
                    new_rule = self.fading["target"]

            # Set new rule without calling set_rule method (would abort fade)
            self.current_rule = int(new_rule)
            self.scheduled_rule = int(new_rule)
            if self.state is True:
                self.send(1)

        # Check if fade complete after step
        if self.fading["target"] == int(self.current_rule):
            # Complete
            self.scheduled_rule = self.current_rule
            self.fading = False

            if self.current_rule == 0:
                self.state = False

        else:
            # Sleep until next step
            next_step = int(self.fading["period"] - ((SoftwareTimer.timer.epoch_now() - self.fading["started"]) % self.fading["period"]))
            SoftwareTimer.timer.create(next_step, self.fade, self.name + "_fade")
