from machine import Pin, SoftI2C
import si7021
import logging
from Sensor import Sensor
import SoftwareTimer

# Set name for module's log lines
log = logging.getLogger("Thermostat")



class Thermostat(Sensor):
    def __init__(self, name, sensor_type, enabled, current_rule, scheduled_rule, mode, tolerance, targets):
        super().__init__(name, sensor_type, enabled, current_rule, scheduled_rule, targets)

        # Setup I2C interface
        self.i2c = SoftI2C(Pin(22), Pin(21))
        self.temp_sensor = si7021.Si7021(self.i2c)

        if mode == "cool":
            self.mode = mode
        elif mode == "heat":
            self.mode = mode
        else:
            raise ValueError

        self.tolerance = float(tolerance)

        self.get_threshold()

        # Store last 3 temperature readings, used to detect failed on/off command
        self.recent_temps = []

        # Check every 30 seconds to detect when changing target state failed (ir command didn't reach ac, etc)
        SoftwareTimer.timer.create(30000, self.audit, self.name)

        log.info(f"Instantiated Thermostat named {self.name}")



    def get_threshold(self):
        if self.current_rule == "Disabled":
            return True

        elif self.mode == "cool":
            self.on_threshold = self.current_rule + self.tolerance
            self.off_threshold = self.current_rule - self.tolerance

        elif self.mode == "heat":
            self.on_threshold = self.current_rule - self.tolerance
            self.off_threshold = self.current_rule + self.tolerance



    def set_rule(self, rule):
        valid = super().set_rule(rule)

        if valid:
            self.get_threshold()
            return True
        else:
            return False



    def fahrenheit(self):
        return si7021.convert_celcius_to_fahrenheit(self.temp_sensor.temperature)



    def condition_met(self):
        current = self.fahrenheit()

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



    # Receive rule from API, validate, set and return True if valid, otherwise return False
    def rule_validator(self, rule):
        try:
            if rule == "Disabled":
                return rule
            # Constrain to range 65-80
            elif 65 <= float(rule) <= 80:
                return float(rule)
            else:
                return False
        except (ValueError, TypeError):
            return False



    # Detects when thermostat fails to turn targets on/off (common with infrared remote)
    # Takes reading every 30 seconds, keeps 3 most recent. Failure detected when all 3 trend in wrong direction
    # Overrides target's state attribute, forcing main loop to re-send on/off command
    def audit(self):
        # Add current temperature reading
        self.recent_temps.append(self.fahrenheit())

        if len(self.recent_temps) > 3:
            # Limit to 3 most recent
            del self.recent_temps[0]

            action = None

            # If 3 most recent readings trend in incorrect direction, assume command was not successful
            if self.recent_temps[0] < self.recent_temps[1] < self.recent_temps[2]:
                if self.mode == "cool" and self.condition_met() == True:
                    print("Failed to start cooling - turning AC on again")
                    log.info("Failed to start cooling - turning AC on again")
                    action = False

                elif self.mode == "heat" and self.condition_met() == False:
                    log.info("Failed to stop heating - turning heater off again")
                    action = True

            elif self.recent_temps[0] > self.recent_temps[1] > self.recent_temps[2]:
                if self.mode == "cool" and self.condition_met() == False:
                    log.info("Failed to stop cooling - turning AC off again")
                    action = True

                elif self.mode == "heat" and self.condition_met() == True:
                    log.info("Failed to start heating - turning heater on again")
                    action = False

            # Override all targets' state attr, allows group to turn on/off again
            if action != None:
                for i in self.targets:
                    i.state = action

            # Force group to turn targets on/off again
            self.group.reset_state()

        # Run again in 30 seconds
        SoftwareTimer.timer.create(30000, self.audit, self.name)
