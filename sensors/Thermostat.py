from machine import Pin, SoftI2C
import time
import si7021
import Sensor
import logging
import uasyncio as asyncio
from Sensor import Sensor

# Set name for module's log lines
log = logging.getLogger("Thermostat")



class Thermostat(Sensor):
    def __init__(self, name, sensor_type, enabled, current_rule, scheduled_rule, targets):
        super().__init__(name, sensor_type, enabled, current_rule, scheduled_rule, targets)

        # Setup I2C interface
        self.i2c = SoftI2C(Pin(22), Pin(21))
        self.temp_sensor = si7021.Si7021(self.i2c)

        log.info(f"Instantiated Thermostat named {self.name}")



    def fahrenheit(self):
        return si7021.convert_celcius_to_fahrenheit(self.temp_sensor.temperature)



    def condition_met(self):
        current = self.fahrenheit()
        if current < (self.current_rule - 1):
            return True
        elif current > (self.current_rule + 1):
            return False
        else:
            return None



    # Receive rule from API, validate, set and return True if valid, otherwise return False
    def set_rule(self, rule):
        try:
            # Constrain to range 65-80
            if 65 <= int(rule) <= 80:
                self.current_rule = int(rule)
                log.info(f"Rule changed to {self.current_rule}")
                return True
            else:
                return False
        except ValueError:
            log.error(f"Failed to change rule to {rule}")
            return False
