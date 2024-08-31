import si7021
import logging
from machine import Pin, SoftI2C
from Thermostat import Thermostat

# Set name for module's log lines
log = logging.getLogger("Si7021")


class Si7021(Thermostat):
    def __init__(self, name, nickname, _type, default_rule, mode, tolerance, units, targets):
        # Setup I2C interface
        self.i2c = SoftI2C(Pin(22), Pin(21))
        self.temp_sensor = si7021.Si7021(self.i2c)

        # Set mode, tolerance, units, current_rule, create monitor task
        super().__init__(name, nickname, _type, default_rule, mode, tolerance, units, targets)
        log.info(f"Instantiated Si7021 named {self.name}")

    # Returns raw temperature reading in Celsius
    # Called by parent class get_temperature method (returns configured units)
    def get_raw_temperature(self):
        return self.temp_sensor.temperature

    # Returns relative humidity percentage
    def get_humidity(self):
        return self.temp_sensor.relative_humidity

    # Return JSON-serializable dict containing all current attributes
    # Called by API get_attributes endpoint, more verbose than status
    def get_attributes(self):
        attributes = super().get_attributes()
        # Remove non-serializable objects
        del attributes["i2c"]
        del attributes["temp_sensor"]
        return attributes
