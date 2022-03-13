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



    # Receive rule from API, validate, set and return True if valid, otherwise return False
    def set_rule(self, rule):
        try:
            # Constrain to range 65-80
            if 65 <= int(rule) <= 80:
                self.current_rule = int(rule)
                return True
            else:
                print("Regex fail")
                return False
        except ValueError:
            print("Try fail")
            return False



    async def loop(self):
        while True:
            current = self.fahrenheit()
            if current < (self.current_rule - 1):
                print(f"Current temp ({current}) less than setting ({self.current_rule})")
                for target in self.targets:
                    # Only send if the target is enabled
                    if self.targets[device]:
                        target.send(1)
            elif current > (self.current_rule + 1):
                print(f"Current temp ({current}) greater than setting ({self.current_rule})")
                for target in self.targets:
                    # Only send if the target is enabled
                    if self.targets[device]:
                        target.send(0)

            # If sensor was disabled
            if not self.loop_started:
                return True # Kill async task

            await asyncio.sleep(15)
