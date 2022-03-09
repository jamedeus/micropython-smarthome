from machine import Pin, SoftI2C
import time
import si7021
import Sensor
import logging
import uasyncio as asyncio
from Sensor import Sensor

# Set log file and syntax
logging.basicConfig(level=logging.INFO, filename='app.log', format='%(asctime)s - %(levelname)s - %(name)s - %(message)s', style='%')
log = logging.getLogger("Thermostat")



class Thermostat(Sensor):
    def __init__(self, name, sensor_type, enabled, current_rule, scheduled_rule, targets):
        super().__init__(name, sensor_type, enabled, current_rule, scheduled_rule, targets)

        # Setup I2C interface
        self.i2c = SoftI2C(Pin(22), Pin(21))
        self.temp_sensor = si7021.Si7021(self.i2c)

        # Force integer
        self.current_rule = int(self.current_rule)

        # Remember if loop is running (prevents multiple asyncio tasks running same loop)
        self.loop_started = False



    def fahrenheit(self):
        return si7021.convert_celcius_to_fahrenheit(self.temp_sensor.temperature)



    async def loop(self):
        while True:
            current = self.fahrenheit()
            if current < (self.current_rule - 1):
                print(f"Current temp ({current}) less than setting ({self.current_rule})")
                for target in self.targets:
                    target.send(1)
            elif current > (self.current_rule + 1):
                print(f"Current temp ({current}) greater than setting ({self.current_rule})")
                for target in self.targets:
                    target.send(0)

            # If sensor was disabled
            if not self.loop_started:
                return True # Kill async task

            await asyncio.sleep(15)
