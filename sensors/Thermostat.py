import asyncio
import logging
from math import isnan
import SoftwareTimer
from Sensor import Sensor

# Set name for module's log lines
log = logging.getLogger("Thermostat")


def fahrenheit_to_celsius(fahrenheit):
    return (fahrenheit - 32) * 5 / 9


def kelvin_to_celsius(kelvin):
    return kelvin - 273.15


def celsius_to_fahrenheit(celsius):
    return celsius * 1.8 + 32


def celsius_to_kelvin(celsius):
    return celsius + 273.15


class Thermostat(Sensor):
    def __init__(self, name, nickname, _type, default_rule, mode, tolerance, units, targets):
        super().__init__(name, nickname, _type, True, default_rule, default_rule, targets)

        # Prevent instantiating with invalid default_rule
        if str(self.default_rule).lower() in ("enabled", "disabled"):
            log.critical(f"{self.name}: Received invalid default_rule: {self.default_rule}")
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

        # Cast initial rule to float, get initial threshold
        self.current_rule = float(self.current_rule)
        self.set_threshold()

        # Store last 3 temperature readings, used to detect failed on/off command (ir command didn't reach ac, etc)
        self.recent_temps = []

        # Track output of condition_met (set by monitor callback)
        self.current = None

        # Start monitor loop (checks temp every 5 seconds)
        asyncio.create_task(self.monitor())

    # Returns current temperature in configured units
    def get_temperature(self):
        try:
            if self.units == "celsius":
                return self.get_raw_temperature()
            elif self.units == "fahrenheit":
                return celsius_to_fahrenheit(self.get_raw_temperature())
            elif self.units == "kelvin":
                return celsius_to_kelvin(self.get_raw_temperature())
        except TypeError:
            return "Error: Unexpected reading from sensor"

    # Placeholder, overwritten by subclasses which support humidity
    def get_humidity(self):
        return "Sensor does not support humidity"

    # Recalculate on/off threshold temperatures after changing set temperature (current_rule)
    def set_threshold(self):
        if self.current_rule == "disabled":
            return True

        elif self.mode == "cool":
            self.on_threshold = float(self.current_rule) + float(self.tolerance)
            self.off_threshold = float(self.current_rule) - float(self.tolerance)

        elif self.mode == "heat":
            self.on_threshold = float(self.current_rule) - float(self.tolerance)
            self.off_threshold = float(self.current_rule) + float(self.tolerance)

    def set_rule(self, rule, scheduled=False):
        valid = super().set_rule(rule)

        if valid:
            self.set_threshold()
            return True
        else:
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

    def condition_met(self):
        current = self.get_temperature()

        if self.mode == "cool":
            if current > self.on_threshold:
                return True
            elif current < self.off_threshold:
                return False

        elif self.mode == "heat":
            if current < self.on_threshold:
                return True
            elif current > self.off_threshold:
                return False

        # No action needed if temperature between on/off thresholds
        return None

    # Check if temperature exceeded threshold every 5 seconds
    async def monitor(self):
        while True:
            self.print(f"Thermostat monitor: {self.get_temperature()}")
            new = self.condition_met()

            # If condition changed, overwrite and refresh group
            if new != self.current and new is not None:
                self.current = new
                self.refresh_group()

            await asyncio.sleep(5)

    # Receives rule from set_rule, returns rule if valid, otherwise returns False
    def validator(self, rule):
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
            else:
                return False
        except (ValueError, TypeError):
            return False

    # Detects when thermostat fails to turn targets on/off (common with infrared remote)
    # Takes reading every 30 seconds, keeps 3 most recent. Failure detected when all 3 trend in wrong direction
    # Overrides group's state attribute, forcing main loop to re-send on/off command
    def audit(self):
        # Add current temperature reading
        self.recent_temps.append(self.get_temperature())

        if len(self.recent_temps) > 3:
            # Limit to 3 most recent
            del self.recent_temps[0]

            action = None

            # If 3 most recent readings trend in incorrect direction, assume command was not successful
            # Flip target device states to reflect failed command (allows loop to turn on/off to correct)
            if self.recent_temps[0] < self.recent_temps[1] < self.recent_temps[2]:
                # Temperature increasing, should be cooling
                if self.mode == "cool" and self.condition_met() is True:
                    self.print("Failed to start cooling - turning AC on again")
                    log.info(f"Failed to start cooling (recent_temps: {self.recent_temps}). Turning AC on again")
                    action = False

                # Temperature increasing, should NOT be heating
                elif self.mode == "heat" and self.condition_met() is False:
                    log.info(f"Failed to stop heating (recent_temps: {self.recent_temps}). Turning heater off again")
                    action = True

            # Neither covered
            elif self.recent_temps[0] > self.recent_temps[1] > self.recent_temps[2]:
                # Temperature decreasing, should NOT be cooling
                if self.mode == "cool" and self.condition_met() is False:
                    log.info(f"Failed to stop cooling (recent_temps: {self.recent_temps}). Turning AC off again")
                    action = True

                # Temperature decreasing, should be heating
                elif self.mode == "heat" and self.condition_met() is True:
                    log.info(f"Failed to start heating (recent_temps: {self.recent_temps}). Turning heater on again")
                    action = False

            # Override all targets' state attr, allows group to turn on/off again
            # State set to opposite of correct state (immediately undone when loop sends turn on/off again)
            if action is not None:
                for i in self.targets:
                    i.state = action

            # Force group to turn targets on/off again
            self.group.reset_state()
            self.refresh_group()

        # Run again in 30 seconds
        SoftwareTimer.timer.create(30000, self.audit, self.name)

    # Called by Config after adding Sensor to Group. Appends functions to Group's post_action_routines list
    # All functions in this list will be called each time the group turns its targets on or off
    def add_routines(self):
        @self.group.add_post_action_routine()
        def restart_audit():
            # Clear recent temps, avoids false positive when cooling starts (readings may take 30-60 sec to drop)
            self.recent_temps = []

            # Cancel and re-create callback, ensures 30 seconds pass before first reading
            # False positive becomes likely if callback runs shortly after change, since only 2 readings are meaningful
            SoftwareTimer.timer.cancel(self.name)
            SoftwareTimer.timer.create(30000, self.audit, self.name)

    # Return JSON-serializable dict containing state information
    # Called by Config.get_status to build API status response
    def get_status(self):
        status = super().get_status()
        status['temp'] = self.get_temperature()
        status['units'] = self.units
        status['humid'] = self.get_humidity()
        return status
