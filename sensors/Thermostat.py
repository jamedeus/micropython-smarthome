from machine import Pin, SoftI2C
import si7021
import logging
from Sensor import Sensor

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

        log.info(f"Instantiated Thermostat named {self.name}")



    def get_threshold(self):
        if self.mode == "cool":
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
