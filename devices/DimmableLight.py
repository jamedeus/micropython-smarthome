import logging
import SoftwareTimer
from Device import Device

# Set name for module's log lines
log = logging.getLogger("DimmableLight")


class DimmableLight(Device):
    def __init__(self, name, nickname, _type, enabled, current_rule, default_rule, min_rule, max_rule):
        super().__init__(name, nickname, _type, enabled, current_rule, default_rule)

        self.min_rule = int(min_rule)
        self.max_rule = int(max_rule)

        # Store parameters in dict while fade in progress
        self.fading = False

        # Prevent instantiating with invalid default_rule
        if str(self.default_rule).lower() in ("enabled", "disabled"):
            log.critical(f"{self.name}: Received invalid default_rule: {self.default_rule}")
            raise AttributeError
        elif int(self.default_rule) > self.max_rule or int(self.default_rule) < self.min_rule:
            raise AttributeError

    def set_rule(self, rule):
        # Check if rule is valid using subclass method - may return a modified rule (ie cast str to int)
        valid_rule = self.rule_validator(rule)
        if str(valid_rule) == "False":
            log.error(f"{self.name}: Failed to change rule to {rule}")
            self.print(f"Failed to change rule to {rule}")
            return False

        elif str(valid_rule).startswith("fade"):
            # Parse fade parameters, start fade (see DimmableLight class)
            return self.start_fade(valid_rule)

        else:
            # Abort fade if user changed brightness in opposite direction
            if isinstance(valid_rule, int) and self.fading:
                if self.fading["down"] and valid_rule > self.current_rule:
                    self.fading = False
                elif not self.fading["down"] and valid_rule < self.current_rule:
                    self.fading = False

            self.current_rule = valid_rule
            self.print(f"Rule changed to {self.current_rule}")
            log.info(f"{self.name}: Rule changed to {self.current_rule}")

            # Abort fade if new rule exceeded target
            self.fade_complete()

            # Update instance attributes to reflect new rule
            self.apply_new_rule()

            return True

    # Takes positive or negative int, adds to self.current_rule
    def increment_rule(self, amount):
        # Throw error if arg is not int
        try:
            amount = int(amount)
        except (ValueError, TypeError):
            return {"ERROR": f"Invalid argument {amount}"}

        # Add amount to current rule
        try:
            new = int(self.current_rule) + int(amount)
        except (ValueError, TypeError):
            return {"ERROR": f"Unable to increment current rule ({self.current_rule})"}

        # Enforce limits
        if new > self.max_rule:
            new = self.max_rule
        if new < self.min_rule:
            new = self.min_rule

        return self.set_rule(new)

    # Base validator for universal, fade, and int rules (replaces parent class)
    def rule_validator(self, rule):
        try:
            # Accept universal rules
            if str(rule).lower() == "enabled" or str(rule).lower() == "disabled":
                return str(rule).lower()

            # Accept fade rules
            # TODO Maybe add a 3rd param "init=False" - will be omitted except by Config. If True, and rule is fade,
            # then check Config.schedule, see when fade was supposed to start, and calculate current position in fade
            elif str(rule).startswith("fade"):
                # Parse parameters from rule
                cmd, target, period = rule.split("/")

                if int(period) < 0:
                    return False

                if self.min_rule <= int(target) <= self.max_rule:
                    return rule
                else:
                    return False

            # Reject "False" before reaching next conditional (would cast to 0 and accept incorrectly)
            elif isinstance(rule, bool):
                return False

            # Accept brightness integer rule
            elif self.min_rule <= int(rule) <= self.max_rule:
                return int(rule)

            # Subclasses may overwrite validator to accept additional rules (default: return False)
            else:
                return self.validator(rule)

        except (ValueError, TypeError):
            return False

    def start_fade(self, valid_rule):
        # Parse parameters from rule
        cmd, target, period = valid_rule.split("/")

        # If first rule on boot is fade, set target as current_rule (animation probably overdue)
        if self.current_rule is None:
            self.current_rule = int(target)
            self.print(f"Rule changed to {self.current_rule}")
            log.info(f"{self.name}: Rule changed to {self.current_rule}")
            return True

        # If rule changes to fade after boot, start fade and return first step as current_rule
        self.print(f"fading to {target} in {period} seconds")
        log.info(f"{self.name}: fading to {target} in {period} seconds")

        # Default to min_rule if device disabled when fade starts
        if self.current_rule == "disabled":
            self.set_rule(self.min_rule)

        if int(target) == self.current_rule:
            self.print("Already at target brightness, skipping fade")
            log.info(f"{self.name}: Already at target brightness, skipping fade")
            return True

        # Find fade direction, get number of steps, period between steps
        if int(target) > self.current_rule:
            steps = int(target) - self.current_rule
            fade_period = int(period) / steps * 1000
            fade_down = False

        elif int(target) < self.current_rule:
            steps = self.current_rule - int(target)
            fade_period = int(period) / steps * 1000
            fade_down = True

        # Ensure device is enabled
        self.enabled = True

        # Create fade timer
        SoftwareTimer.timer.create(fade_period, self.fade, self.name + "_fade")

        # Store fade parameters in dict, used by fade method below
        self.fading = {
            "started": SoftwareTimer.timer.epoch_now(),
            "starting_brightness": self.current_rule,
            "target": int(target),
            "period": fade_period,
            "down": fade_down
        }

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

        # Fade complete if rule is no longer int (changed to enabled, disabled, etc)
        if not isinstance(self.current_rule, int):
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

    # Return JSON-serializable dict containing state information
    # Called by Config.get_status to build API status response
    def get_status(self):
        status = super().get_status()
        status['min_rule'] = self.min_rule
        status['max_rule'] = self.max_rule
        return status
