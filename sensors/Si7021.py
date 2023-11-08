import si7021
import logging
from machine import Pin, SoftI2C
from Thermostat import Thermostat

# Set name for module's log lines
log = logging.getLogger("Si7021")


class Si7021(Thermostat):
    def __init__(self, name, nickname, _type, default_rule, mode, tolerance, targets):
        # Setup I2C interface
        self.i2c = SoftI2C(Pin(22), Pin(21))
        self.temp_sensor = si7021.Si7021(self.i2c)

        # Set mode, tolerance, rule, create monitor task
        super().__init__(name, nickname, _type, default_rule, mode, tolerance, targets)
        log.info(f"Instantiated Si7021 named {self.name}")

    def fahrenheit(self):
        return si7021.convert_celcius_to_fahrenheit(self.temp_sensor.temperature)

    # Return JSON-serializable dict containing state information
    # Called by Config.get_status to build API status response
    def get_status(self):
        status = super().get_status()
        status['temp'] = self.fahrenheit()
        status['humid'] = self.temp_sensor.relative_humidity
        return status
