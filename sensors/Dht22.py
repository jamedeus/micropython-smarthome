import dht
import logging
from machine import Pin
from Thermostat import Thermostat

# Set name for module's log lines
log = logging.getLogger("Dht22")


class Dht22(Thermostat):
    def __init__(self, name, nickname, _type, default_rule, mode, tolerance, units, targets, pin):
        # Instantiate pin and sensor driver
        self.temp_sensor = dht.DHT22(Pin(int(pin)))

        # Set mode, tolerance, units, current_rule, create monitor task
        super().__init__(name, nickname, _type, default_rule, mode, tolerance, units, targets)
        log.info(f"Instantiated Dht22 named {self.name}")

    # Returns raw temperature reading in Celsius
    # Called by parent class get_temperature method (returns configured units)
    def get_raw_temperature(self):
        self.temp_sensor.measure()
        return self.temp_sensor.temperature()

    # Returns relative humidity percentage
    def get_humidity(self):
        self.temp_sensor.measure()
        return self.temp_sensor.humidity()
