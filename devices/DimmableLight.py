import logging
import SoftwareTimer
from Device import Device

# Set name for module's log lines
log = logging.getLogger("DimmableLight")


class DimmableLight(Device):
    '''Base class for all devices which support a range of brightness levels.
    Inherits from Device and adds attributes and methods specific to dimmable
    lights (increment_rule method, methods to gradually fade to new brightness,
    validator accepts integer rules within supported range and fade rules).

    Args:
      name:         Unique, sequential config name (device1, device2, etc)
      nickname:     User-configured friendly name shown on frontend
      _type:        Instance type, determines driver class and frontend UI
      enabled:      Initial enable state (True or False)
      current_rule: Initial rule, has different effects depending on subclass
      default_rule: Fallback rule used when no other valid rules are available
      min_rule:     The minimum supported integer rule, used by rule validator
      max_rule:     The maximum supported integer rule, used by rule validator

    Subclassed by all dimmable light device drivers, cannot be used standalone.
    Subclasses must implement send method (takes bool argument, turns device ON
    if True, turns device OFF if False).

    The min_rule and max_rule attributes determine the range of supported int
    rules. The web frontend scales this range to 1-100 for visual consistency,
    effectively showing the max brightness percentage instead of literal rule.

    Supports universal rules ("enabled" and "disabled"), brightness rules (int
    between min_rule and max_rule arguments), and fade rules
    (syntax: fade/target_rule/duration_seconds).
    The default_rule must be an integer or fade (not universal rule).
    '''

    def __init__(self, name, nickname, _type, enabled, current_rule, default_rule, min_rule, max_rule):
        super().__init__(name, nickname, _type, enabled, current_rule, default_rule)

        self.min_rule = int(min_rule)
        self.max_rule = int(max_rule)

        # Store parameters in dict while fade in progress
        self.fading = False

        # Prevent instantiating with invalid default_rule
        if str(self.default_rule).lower() in ("enabled", "disabled"):
            log.critical(
                "%s: Received invalid default_rule: %s",
                self.name, self.default_rule
            )
            raise AttributeError
        elif int(self.default_rule) > self.max_rule or int(self.default_rule) < self.min_rule:
            raise AttributeError

    def set_rule(self, rule, scheduled=False):
        '''Takes new rule, validates, if valid sets as current_rule (and
        scheduled_rule if scheduled arg is True) and calls apply_new_rule.

        Args:
          rule:      The new rule, will be set as current_rule if valid
          scheduled: Optional, if True also sets scheduled_rule if rule valid

        If fade rule received (syntax: fade/target_rule/duration_seconds) calls
        start_fade method (creates interrupts that run when each step is due).

        Aborts in-progress fade if it receives an integer rule that causes rule
        to move in opposite direction of fade (eg if new rule is greater than
        current_rule while fading down).
        '''

        # Check if rule is valid (may return modified rule, eg cast str to int)
        valid_rule = self.rule_validator(rule)
        if valid_rule is False:
            log.error("%s: Failed to change rule to %s", self.name, rule)
            self.print(f"Failed to change rule to {rule}")
            return False

        elif str(valid_rule).startswith("fade"):
            # Parse fade parameters, start fade
            return self.start_fade(valid_rule, scheduled)

        else:
            # Abort fade if user changed brightness in opposite direction
            if isinstance(valid_rule, int) and self.fading:
                if self.fading["down"] and valid_rule > self.current_rule:
                    self.fading = False
                elif not self.fading["down"] and valid_rule < self.current_rule:
                    self.fading = False

            # If called by next_rule: set scheduled_rule
            if scheduled:
                self.scheduled_rule = valid_rule

            self.current_rule = valid_rule
            self.print(f"Rule changed to {self.current_rule}")
            log.info("%s: Rule changed to %s", self.name, self.current_rule)

            # Abort fade if new rule exceeded target
            self.fade_complete()

            # Update instance attributes to reflect new rule
            self.apply_new_rule()

            return True

    def increment_rule(self, amount):
        '''Takes positive or negative integer, adds to current_rule and calls
        set_rule method. Throws error if current_rule is not an integer.
        '''

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

    def rule_validator(self, rule):
        '''Accepts universal rules ("enabled" and "disabled"), integer rules
        between self.min_rule and self.max_rule, and rules that start gradual
        fade (syntax: fade/target_rule/duration_seconds).

        Takes rule, returns rule if valid (may return modified rule, eg cast to
        lowercase), return False if rule is invalid.

        Can be extended to support other rules by replacing the validator
        method (called if rule is neither "enabled" nor "disabled").
        '''

        '''Base validator for universal, fade, and int rules (replaces parent class)'''

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

    def start_fade(self, valid_rule, scheduled=False):
        '''Called by set_rule when it receives a fade rule. Calculates number
        of steps to reach target brightness and delay between each step, saves
        in self.fading attribute (dict), and creates interrupt to update rule
        when each step is due. If scheduled arg is True each step also updates
        scheduled_rule.
        '''

        # Parse parameters from rule
        cmd, target, period = valid_rule.split("/")

        # If first rule on boot is fade, set target as current_rule (animation probably overdue)
        if self.current_rule is None:
            self.current_rule = int(target)
            self.print(f"Rule changed to {self.current_rule}")
            log.info("%s: Rule changed to %s", self.name, self.current_rule)
            return True

        # If rule changes to fade after boot, start fade and return first step as current_rule
        self.print(f"fading to {target} in {period} seconds")
        log.info("%s: fading to %s in %s seconds", self.name, target, period)

        # Default to min_rule if device disabled when fade starts
        if self.current_rule == "disabled":
            self.set_rule(self.min_rule)

        if int(target) == self.current_rule:
            self.print("Already at target brightness, skipping fade")
            log.info("%s: Already at target brightness, skipping fade", self.name)
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
            "down": fade_down,
            "scheduled": scheduled
        }

        return True

    def fade_complete(self):
        '''Cleanup and return True if fade is complete, return False if not.
        Fade is complete when current_rule matches or exceeds fade target.
        If called when a scheduled fade is aborted sets scheduled_rule to fade
        target even if target was not reached.
        '''

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
            # If scheduled fade: set scheduled_rule to target
            if self.fading["scheduled"]:
                self.scheduled_rule = self.fading["target"]
            self.fading = False

            if self.current_rule == 0:
                self.state = False
            return True

        # When fading up: complete if current_rule equal or greater than target
        elif not self.fading["down"] and self.current_rule >= self.fading["target"]:
            # If scheduled fade: set scheduled_rule to target
            if self.fading["scheduled"]:
                self.scheduled_rule = self.fading["target"]
            self.fading = False
            return True

        # Fade not complete
        else:
            return False

    def fade(self):
        '''Called by SoftwareTimer when each step of ongoing fade is due.
        Updates current_rule (and scheduled_rule if start_fade was called with
        scheduled arg), calls send method so new brightness takes effect, and
        checks if fade is complete (creates next interrupt if not complete).
        '''

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

            # If fade started by schedule rule: update scheduled_rule
            if self.fading["scheduled"]:
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

    def get_status(self):
        '''Return JSON-serializable dict containing status information.
        Called by Config.get_status to build API status endpoint response.
        Contains all attributes displayed on the web frontend.
        '''
        status = super().get_status()
        status['min_rule'] = self.min_rule
        status['max_rule'] = self.max_rule
        return status
