import dht
import logging
from machine import Pin
from Thermostat import Thermostat

# Set name for module's log lines
log = logging.getLogger("Dht22")


class Dht22(Thermostat):
    def __init__(self, name, nickname, _type, default_rule, mode, tolerance, targets, pin):
        # Instantiate pin and sensor driver
        self.temp_sensor = dht.DHT22(Pin(int(pin)))

        # Set mode, tolerance, rule, create monitor task
        super().__init__(name, nickname, _type, default_rule, mode, tolerance, targets)
        log.info(f"Instantiated Dht22 named {self.name}")

    def fahrenheit(self):
        self.temp_sensor.measure()
        return self.temp_sensor.temperature() * 1.8 + 32

    # Return JSON-serializable dict containing state information
    # Called by Config.get_status to build API status response
    def get_status(self):
        status = super().get_status()
        status['temp'] = self.fahrenheit()
        status['humid'] = self.temp_sensor.humidity()
        return status
