import logging
import SoftwareTimer
from Device import Device

# Set name for module's log lines
log = logging.getLogger("DimmableLight")


class DimmableLight(Device):
    def __init__(self, name, nickname, _type, enabled, current_rule, default_rule, min_bright, max_bright):
        super().__init__(name, nickname, _type, enabled, current_rule, default_rule)

        self.min_bright = int(min_bright)
        self.max_bright = int(max_bright)

        if int(self.default_rule) > self.max_bright or int(self.default_rule) < self.min_bright:
            raise AttributeError

        # Store parameters in dict while fade in progress
        self.fading = False

    def start_fade(self, valid_rule):
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

        # Store fade direction, determines if fade aborts when user changes brightness
        if self.fading["target"] < self.fading["starting_brightness"]:
            self.fading["down"] = True
        else:
            self.fading["down"] = False

        # Return starting point (will be set as current rule by device.set_rule)
        return True

    # Cleanup and return True if fade is complete, return False if not
    # Fade is complete when current_rule matches or exceeds fade target
    # A user-changed rule will stop the fade, but will not overwrite scheduled_rule (target used)
    # TODO user-initiated fade will break scheduled_rule
    def fade_complete(self):
        # Fade complete if device disabled mid-fade, or called when not fading
        if not self.enabled or not self.fading:
            self.fading = False
            return True

        # When fading down: complete if current_rule equal or less than target
        if self.fading["down"] and self.current_rule <= self.fading["target"]:
            self.scheduled_rule = self.fading["target"]
            self.fading = False

            if self.current_rule == 0:
                self.state = False
            return True

        # When fading up: complete if current_rule equal or greater than target
        elif not self.fading["down"] and self.current_rule >= self.fading["target"]:
            self.scheduled_rule = self.fading["target"]
            self.fading = False
            return True

        # Fade not complete
        else:
            return False

    # Called by SoftwareTimer during fade animation, initialized in rule_validator above
    def fade(self):
        # Fade to next step (unless fade already complete)
        if not self.fade_complete():
            # Use starting time, current time, period (time per step) to determine how many steps should have been taken
            steps = (SoftwareTimer.timer.epoch_now() - self.fading["started"]) // self.fading["period"]

            # Fading up
            if not self.fading["down"]:
                new_rule = self.fading["starting_brightness"] + steps
                if new_rule > self.fading["target"]:
                    new_rule = self.fading["target"]

            # Fading down
            elif self.fading["down"]:
                new_rule = self.fading["starting_brightness"] + steps * -1
                if new_rule < self.fading["target"]:
                    new_rule = self.fading["target"]

            self.scheduled_rule = int(new_rule)

            # Don't override user-set brightness
            if (self.fading["down"] and int(new_rule) < self.current_rule) or (not self.fading["down"] and int(new_rule) > self.current_rule):
                # Set new rule without calling set_rule method (would abort fade)
                self.current_rule = int(new_rule)
                if self.state is True:
                    self.send(1)

        # Start timer for next step (unless fade already complete)
        if not self.fade_complete():
            # Sleep until next step
            next_step = int(self.fading["period"] - ((SoftwareTimer.timer.epoch_now() - self.fading["started"]) % self.fading["period"]))
            SoftwareTimer.timer.create(next_step, self.fade, self.name + "_fade")
