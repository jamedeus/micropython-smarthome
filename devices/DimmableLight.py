import app_context
from Device import Device


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

    def __init__(self, name, nickname, _type, enabled, default_rule, min_rule, max_rule):
        super().__init__(name, nickname, _type, enabled, default_rule)

        self.min_rule = int(min_rule)
        self.max_rule = int(max_rule)

        # Store parameters in dict while fade in progress
        self.fading = False

        # Prevent instantiating with invalid default_rule
        if str(self.default_rule).lower() in ("enabled", "disabled"):
            self.log.critical("Invalid default_rule: %s", self.default_rule)
            raise AttributeError
        if int(self.default_rule) > self.max_rule:
            self.log.critical(
                "default_rule (%s) cannot be greater than max_rule (%s)",
                self.default_rule, self.max_rule
            )
            raise AttributeError
        if int(self.default_rule) < self.min_rule:
            self.log.critical(
                "default_rule (%s) must be greater than min_rule (%s)",
                self.default_rule, self.min_rule
            )
            raise AttributeError

    def set_rule(self, rule, scheduled=False):
        '''Takes new rule, validates, if valid sets as current_rule (and
        scheduled_rule if scheduled arg is True) and calls apply_new_rule.

        Args:
          rule:      The new rule, will be set as current_rule if valid
          scheduled: Optional, if True also sets scheduled_rule if rule valid

        If fade rule received (syntax: fade/target_rule/duration_seconds) calls
        _start_fade method (creates interrupts that run when each step is due).

        Aborts in-progress fade if it receives an integer rule that causes rule
        to move in opposite direction of fade (eg if new rule is greater than
        current_rule while fading down).
        '''
        self.log.debug(
            "set_rule called with %s (scheduled=%s)",
            rule, scheduled
        )

        # Check if rule is valid (may return modified rule, eg cast str to int)
        valid_rule = self.rule_validator(rule)
        if valid_rule is False:
            self.log.error("Failed to change rule to %s", rule)
            self.print(f"Failed to change rule to {rule}")
            return False

        if str(valid_rule).startswith("fade"):
            # Parse fade parameters, start fade
            return self._start_fade(valid_rule, scheduled)

        # Abort fade if user changed brightness in opposite direction
        if isinstance(valid_rule, int) and self.fading:
            if self.fading["down"] and valid_rule > self.current_rule:
                self.log.debug("abort fade")
                self.fading = False
            elif not self.fading["down"] and valid_rule < self.current_rule:
                self.log.debug("abort fade")
                self.fading = False

        # If called by next_rule: set scheduled_rule
        if scheduled:
            self.scheduled_rule = valid_rule

        self.current_rule = valid_rule
        self.print(f"Rule changed to {self.current_rule}")
        self.log.info("Rule changed to %s", self.current_rule)

        # Abort fade if new rule exceeded target
        self._fade_complete()

        # Update instance attributes to reflect new rule
        self.apply_new_rule()

        return True

    def increment_rule(self, amount):
        '''Takes positive or negative integer, adds to current_rule and calls
        set_rule method. Throws error if current_rule is not an integer.
        '''
        self.log.debug("increment_rule called with %s", amount)

        # Throw error if arg is not int
        try:
            amount = int(amount)
        except (ValueError, TypeError):
            self.log.error("increment_rule: invalid argument: %s", amount)
            return {"ERROR": f"Invalid argument {amount}"}

        # Add amount to current rule
        try:
            new = int(self.current_rule) + int(amount)
        except (ValueError, TypeError):
            self.log.error(
                "Unable to increment current rule (%s)",
                self.current_rule
            )
            return {"ERROR": f"Unable to increment current rule ({self.current_rule})"}

        # Enforce limits
        new = min(new, self.max_rule)
        new = max(new, self.min_rule)

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

        try:
            # Accept universal rules
            if str(rule).lower() in ("enabled", "disabled"):
                return str(rule).lower()

            # Accept fade rules
            # TODO Maybe add 3rd param "init=False" - will be omitted except by
            # Config. If True and rule is fade, check Config.schedule, see when
            # fade was supposed to start, calculate current position in fade
            if str(rule).startswith("fade"):
                # Parse parameters from rule
                _, target, period = rule.split("/")

                if int(period) < 0:
                    return False

                if self.min_rule <= int(target) <= self.max_rule:
                    return rule
                return False

            # Reject "False" before reaching next conditional (would cast to
            # 0 and accept incorrectly)
            if isinstance(rule, bool):
                return False

            # Accept brightness integer rule
            if self.min_rule <= int(rule) <= self.max_rule:
                return int(rule)

            # Subclasses may overwrite validator to accept additional rules
            # (default: return False)
            return self.validator(rule)

        except (ValueError, TypeError):
            return False

    def _start_fade(self, valid_rule, scheduled=False):
        '''Called by set_rule when it receives a fade rule. Calculates number
        of steps to reach target brightness and delay between each step, saves
        in self.fading attribute (dict), and creates interrupt to update rule
        when each step is due. If scheduled arg is True each step also updates
        scheduled_rule.
        '''
        self.log.debug(
            "_start_fade called with %s (scheduled=%s)",
            valid_rule, scheduled
        )

        # Parse parameters from rule
        _, target, period = valid_rule.split("/")

        # If first rule on boot is fade, set target as current_rule and
        # scheduled_rule (fade animation probably overdue)
        if self.current_rule is None:
            self.current_rule = int(target)
            self.scheduled_rule = int(target)
            self.print(f"Rule changed to {self.current_rule}")
            self.log.info("Rule changed to %s", self.current_rule)
            return True

        # If rule changes to fade after boot, start fade
        self.print(f"fading to {target} in {period} seconds")
        self.log.info("fading to %s in %s seconds", target, period)

        # Default to min_rule if device disabled when fade starts
        if self.current_rule == "disabled":
            self.set_rule(self.min_rule)

        # Find fade direction, get number of steps, period between steps
        if int(target) > self.current_rule:
            steps = int(target) - self.current_rule
            fade_period = int(period) / steps * 1000
            fade_down = False

        elif int(target) < self.current_rule:
            steps = self.current_rule - int(target)
            fade_period = int(period) / steps * 1000
            fade_down = True

        else:
            self.print("Already at target brightness, skipping fade")
            self.log.info("Already at target brightness, skipping fade")
            return True

        # Ensure device is enabled
        self.enabled = True

        # Create fade timer
        app_context.timer_instance.create(
            fade_period,
            self.fade,
            self.name + "_fade"
        )

        # Store fade parameters in dict, used by fade method below
        self.fading = {
            "started": app_context.timer_instance.epoch_now(),
            "starting_brightness": self.current_rule,
            "target": int(target),
            "period": fade_period,
            "down": fade_down,
            "scheduled": scheduled
        }
        self.log.debug("fade parameters: %s", self.fading)

        return True

    def _fade_complete(self):
        '''Cleanup and return True if fade is complete, return False if not.
        Fade is complete when current_rule matches or exceeds fade target.
        If called when a scheduled fade is aborted sets scheduled_rule to fade
        target even if target was not reached.
        '''

        # Fade complete if device disabled mid-fade, or called when not fading
        if not self.enabled or not self.fading:
            self.log.debug("fade complete (disabled or not fading)")
            self.fading = False
            return True

        # Fade complete if rule is no longer int (changed to enabled/disabled)
        if not isinstance(self.current_rule, int):
            self.log.debug("fade complete (rule no longer int)")
            self.fading = False
            return True

        # When fading down: complete if current_rule equal or less than target
        if self.fading["down"] and self.current_rule <= self.fading["target"]:
            self.log.debug("fade complete (target reached)")
            # If scheduled fade: set scheduled_rule to target
            if self.fading["scheduled"]:
                self.scheduled_rule = self.fading["target"]
            self.fading = False

            if self.current_rule == 0:
                self.state = False
            return True

        # When fading up: complete if current_rule equal or greater than target
        if not self.fading["down"] and self.current_rule >= self.fading["target"]:
            self.log.debug("fade complete (target reached)")
            # If scheduled fade: set scheduled_rule to target
            if self.fading["scheduled"]:
                self.scheduled_rule = self.fading["target"]
            self.fading = False
            return True

        # Fade not complete
        return False

    def fade(self):
        '''Called by SoftwareTimer when each step of ongoing fade is due.
        Updates current_rule (and scheduled_rule if _start_fade was called with
        scheduled arg), calls send method so new brightness takes effect, and
        checks if fade is complete (creates next interrupt if not complete).
        '''

        # Fade to next step (unless fade already complete)
        if not self._fade_complete():
            # Use starting time, current time, period (time per step) to
            # determine how many steps should have been taken
            steps = (
                app_context.timer_instance.epoch_now() - self.fading["started"]
            ) // self.fading["period"]

            # Fading down
            if self.fading["down"]:
                new_rule = self.fading["starting_brightness"] + steps * -1
                new_rule = max(new_rule, self.fading['target'])

            # Fading up
            else:
                new_rule = self.fading["starting_brightness"] + steps
                new_rule = min(new_rule, self.fading['target'])

            # If fade started by schedule rule: update scheduled_rule
            if self.fading["scheduled"]:
                self.scheduled_rule = int(new_rule)

            # Don't override user-set brightness
            if (
                (self.fading["down"] and int(new_rule) < self.current_rule)
                or (not self.fading["down"] and int(new_rule) > self.current_rule)
            ):
                # Set new rule without calling set_rule method (would abort fade)
                self.current_rule = int(new_rule)
                if self.state is True:
                    self.send(1)

        # Start timer for next step (unless fade already complete)
        if not self._fade_complete():
            # Sleep until next step
            next_step = int(self.fading["period"] - ((
                app_context.timer_instance.epoch_now() - self.fading["started"]
            ) % self.fading["period"]))
            app_context.timer_instance.create(
                next_step,
                self.fade,
                self.name + "_fade"
            )

    def get_status(self):
        '''Return JSON-serializable dict containing status information.
        Called by Config.get_status to build API status endpoint response.
        Contains all attributes displayed on the web frontend.
        '''
        status = super().get_status()
        status['min_rule'] = self.min_rule
        status['max_rule'] = self.max_rule
        return status
