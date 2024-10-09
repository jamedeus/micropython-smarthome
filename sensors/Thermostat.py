import asyncio
from math import isnan
import SoftwareTimer
from SensorWithLoop import SensorWithLoop


def fahrenheit_to_celsius(fahrenheit):
    '''Takes temperature in fahrenheit, converts to celsius and returns.'''
    return (fahrenheit - 32) * 5 / 9


def kelvin_to_celsius(kelvin):
    '''Takes temperature in kelvin, converts to celsius and returns.'''
    return kelvin - 273.15


def celsius_to_fahrenheit(celsius):
    '''Takes temperature in celsius, converts to fahrenheit and returns.'''
    return celsius * 1.8 + 32


def celsius_to_kelvin(celsius):
    '''Takes temperature in celsius, converts to kelvin and returns.'''
    return celsius + 273.15


class Thermostat(SensorWithLoop):
    '''Base class for all temperature sensors. Inherits from SensorWithLoop
    and adds attributes and methods to use the sensor as a thermostat (turn
    devices on and off when a configurable temperature threshold is crossed).

    Args:
      name:         Unique, sequential config name (device1, device2, etc)
      nickname:     User-configured friendly name shown on frontend
      _type:        Instance type, determines driver class and frontend UI
      enabled:      Initial enable state (True or False)
      default_rule: Fallback rule used when no other valid rules are available
      mode:         Must be "cool" (turn on when temperature > current_rule) or
                    "heat" (turn on when temperature < current_rule)
      tolerance:    Number between 0.1 and 10, determines buffer above and
                    below current_rule where devices are not turned on or off
      units:        Must be "celsius", "fahrenheit", or "kelvin"
      targets:      List of device names (device1 etc) controlled by sensor

    Subclassed by all temperature sensor drivers, cannot be used standalone.
    Subclasses must implement a get_raw_temperature method (returns current
    temperature reading). Drivers for sensors which detect humidity may also
    implement a get_humidity method (returns current humidity reading).

    Supports universal rules ("enabled" and "disabled") and temperature cutoff
    rules (float between 18 and 27 celsius or equivalent in configured units).
    The default_rule must be a float (not universal rule).
    '''

    def __init__(self, name, nickname, _type, default_rule, mode, tolerance, units, targets):
        super().__init__(name, nickname, _type, True, default_rule, targets)

        # Prevent instantiating with invalid default_rule
        if str(self.default_rule).lower() in ("enabled", "disabled"):
            self.log.critical("Invalid default_rule: %s", self.default_rule)
            raise AttributeError

        # Set cooling or heating mode, determines when targets turn on/off
        # Cooling: Turn ON when measured temp exceeds rule, turn OFF when below rule
        # Heating: Turn OFF when measured temp exceeds rule, turn ON when below rule
        if mode.lower() in ["cool", "heat"]:
            self.mode = mode.lower()
        else:
            raise ValueError

        # Set temperature units
        if units.lower() in ["celsius", "fahrenheit", "kelvin"]:
            self.units = units.lower()
        else:
            raise ValueError

        # Tolerance determines on/off thresholds (current_rule +/- tolerance)
        self.tolerance = float(tolerance)

        # On and off temperature thresholds (calculated when set_rule called)
        self.on_threshold = None
        self.off_threshold = None

        # Store last 3 temperature readings, used to detect failed on/off
        # command (ir command didn't reach ac, etc)
        self.recent_temps = []

        # Track output of condition_met (set by monitor coro, calls
        # refresh_group when current changes instead of every read)
        self.current = None

        # Start monitor loop (checks temp every 5 seconds)
        self.monitor_task = asyncio.create_task(self.monitor())

    def get_temperature(self):
        '''Returns current temperature reading in configured units.'''

        try:
            if self.units == "celsius":
                return self.get_raw_temperature()
            if self.units == "fahrenheit":
                return celsius_to_fahrenheit(self.get_raw_temperature())
            if self.units == "kelvin":
                return celsius_to_kelvin(self.get_raw_temperature())
            raise ValueError(
                'Unsupported mode (must be "celsius", "fahrenheit", or "kelvin")'
            )
        except TypeError:
            return "Error: Unexpected reading from sensor"

    def get_raw_temperature(self):
        '''Placeholder method - subclasses must implement method which returns
        current temperature reading in celsius.
        '''
        raise NotImplementedError('Must be implemented in subclass')

    def get_humidity(self):
        '''Placeholder function, replaced by subclasses which support humidity.'''

        return "Sensor does not support humidity"

    def set_threshold(self):
        '''Calculates on and off temperature thresholds based on current_rule
        and tolerance attribute. Called after changing current_rule.
        '''
        if self.current_rule == "disabled":
            return

        if self.mode == "cool":
            self.on_threshold = float(self.current_rule) + float(self.tolerance)
            self.off_threshold = float(self.current_rule) - float(self.tolerance)

        elif self.mode == "heat":
            self.on_threshold = float(self.current_rule) - float(self.tolerance)
            self.off_threshold = float(self.current_rule) + float(self.tolerance)

        else:
            raise ValueError('Unsupported mode (must be "cool" or "heat")')

        self.log.debug(
            "set_threshold: on_threshold=%s, off_threshold=%s",
            self.on_threshold, self.off_threshold
        )

    def set_rule(self, rule, scheduled=False):
        '''Takes new rule, validates, if valid sets as current_rule (and
        scheduled_rule if scheduled arg is True) and calls apply_new_rule.

        Args:
          rule:      The new rule, will be set as current_rule if valid
          scheduled: Optional, if True also sets scheduled_rule if rule valid
        '''
        valid = super().set_rule(rule, scheduled)

        if valid:
            self.set_threshold()
            return True
        return False

    def increment_rule(self, amount):
        '''Takes positive or negative float, adds to current_rule and calls
        set_rule method. Throws error if current_rule is not an int or float.
        '''
        self.log.debug("increment_rule called with %s", amount)

        # Throw error if arg is not int or float
        try:
            amount = float(amount)
            if isnan(amount):
                raise ValueError
        except (ValueError, TypeError):
            self.log.error("increment_rule: invalid argument: %s", amount)
            return {"ERROR": f"Invalid argument {amount}"}

        # Add amount to current rule
        try:
            new = float(self.current_rule) + amount
        except (ValueError, TypeError):
            self.log.error(
                "Unable to increment current rule (%s)",
                self.current_rule
            )
            return {"ERROR": f"Unable to increment current rule ({self.current_rule})"}

        return self.set_rule(new)

    def condition_met(self):
        '''Returns True if current temperature exceeds configured on_threshold.
        Returns False if current temperature exceeds configured off_threshold.
        Returns None if current temperature is between on and off thresholds.
        '''
        current = self.get_temperature()

        if self.mode == "cool":
            if current > self.on_threshold:
                return True
            if current < self.off_threshold:
                return False

        elif self.mode == "heat":
            if current < self.on_threshold:
                return True
            if current > self.off_threshold:
                return False

        # No action needed if temperature between on/off thresholds
        return None

    async def monitor(self):
        '''Async coroutine, checks temperature every 5 seconds and turns target
        devices on or off if on_threshold or off_threshold exceeded.
        '''
        self.log.debug("Starting Thermostat.monitor coro")
        try:
            while True:
                self.log.debug("temperature: %s", self.get_temperature())
                new = self.condition_met()

                # If condition changed, overwrite and refresh group
                if new != self.current and new is not None:
                    self.log.debug(
                        "monitor: condition changed from %s to %s",
                        self.current, new
                    )
                    self.current = new
                    self.refresh_group()

                await asyncio.sleep(5)

        # Sensor disabled, exit loop
        except asyncio.CancelledError:
            self.log.debug("Exiting Thermostat.monitor coro")
            return False

    def validator(self, rule):
        '''Accepts any integer or float between 18 and 27 celsius (or
        equivalent in configured units).
        '''
        try:
            # Convert rule to celsius if using different units
            if self.units == 'fahrenheit':
                converted_rule = round(fahrenheit_to_celsius(float(rule)), 1)
            elif self.units == 'kelvin':
                converted_rule = round(kelvin_to_celsius(float(rule)), 1)
            else:
                converted_rule = rule

            # Constrain to range 18-27 celsius
            if 18 <= float(converted_rule) <= 27:
                # Return in original units if valid
                return float(rule)
            # Rule out of range
            return False
        except (ValueError, TypeError):
            return False

    def audit(self):
        '''Detects when thermostat fails to turn target devices on/off (common
        with infrared remote controlling AC or heater) and overrides group's
        state to force the main loop to re-send on/off command.

        Takes reading every 30 seconds, keeps 3 most recent readings, detects
        failure when all 3 trend in wrong direction (eg temperature is rising
        while thermostat is in cool mode and AC should be turned on).
        '''

        # Add current temperature reading
        self.recent_temps.append(self.get_temperature())

        if len(self.recent_temps) > 3:
            # Limit to 3 most recent
            del self.recent_temps[0]

            action = None

            # If last 3 readings trend in incorrect direction, assume command failed
            if self.recent_temps[0] < self.recent_temps[1] < self.recent_temps[2]:
                # Temperature increasing, should be cooling
                if self.mode == "cool" and self.condition_met() is True:
                    self.print("Failed to start cooling - turning AC on again")
                    self.log.info(
                        "Failed to start cooling (recent_temps: %s). Turning AC on again",
                        self.recent_temps
                    )
                    action = False

                # Temperature increasing, should NOT be heating
                elif self.mode == "heat" and self.condition_met() is False:
                    self.log.info(
                        "Failed to stop heating (recent_temps: %s). Turning heater off again",
                        self.recent_temps
                    )
                    action = True

            elif self.recent_temps[0] > self.recent_temps[1] > self.recent_temps[2]:
                # Temperature decreasing, should NOT be cooling
                if self.mode == "cool" and self.condition_met() is False:
                    self.log.info(
                        "Failed to stop cooling (recent_temps: %s). Turning AC off again",
                        self.recent_temps
                    )
                    action = True

                # Temperature decreasing, should be heating
                elif self.mode == "heat" and self.condition_met() is True:
                    self.log.info(
                        "Failed to start heating (recent_temps: %s). Turning heater on again",
                        self.recent_temps
                    )
                    action = False

            # Override all targets' state attr with opposite of correct state
            # (allows group to turn on/off again, state immediately undone when
            # group refresh method calls apply_action)
            if action is not None:
                for i in self.targets:
                    self.log.debug("set %s state to %s", i.name, action)
                    i.state = action

            # Force group to turn targets on/off again
            self.group.reset_state()
            self.refresh_group()

        # Run again in 30 seconds
        SoftwareTimer.timer.create(30000, self.audit, self.name)

    def add_routines(self):
        '''Called by Config.build_groups after Sensor is added to Group, adds
        audit function to Group's post_action_routines list (detects when
        target devices fail to turn on and forces group to resend command).
        '''
        @self.group.add_post_action_routine()
        def restart_audit():
            # Clear recent temps, avoids false positive when cooling starts
            # (temperature may take 30-60 sec to drop when AC turns on)
            self.recent_temps = []

            # Cancel and re-create callback (ensure 30 seconds pass before first reading)
            # Reduces chance of false positives (more likely if reading taken immediately
            # when target turns on, temp hasn't changed yet so only 2 readings meaningful)
            SoftwareTimer.timer.create(30000, self.audit, self.name)

    def get_status(self):
        '''Return JSON-serializable dict containing status information.
        Called by Config.get_status to build API status endpoint response.
        Contains all attributes displayed on the web frontend.
        '''
        status = super().get_status()
        status['temp'] = self.get_temperature()
        status['units'] = self.units
        status['humid'] = self.get_humidity()
        return status
