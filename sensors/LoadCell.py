import logging
from math import isnan
from machine import Pin
import uasyncio as asyncio
from hx711 import HX711
from Sensor import Sensor

# Set name for module's log lines
log = logging.getLogger("Load_Cell")


class LoadCell(Sensor):
    def __init__(self, name, nickname, _type, default_rule, targets, pin_data, pin_clock):
        super().__init__(name, nickname, _type, True, None, default_rule, targets)

        # Instantiate sensor, tare
        data = Pin(int(pin_data), Pin.IN, Pin.PULL_DOWN)
        clock = Pin(int(pin_clock), Pin.OUT)
        self.sensor = HX711(clock, data)
        self.tare_sensor()

        # Track output of condition_met (set by monitor callback)
        self.current = None

        # Start monitor loop (checks if threshold met every second)
        asyncio.create_task(self.monitor())

        log.info(f"Instantiated load cell sensor named {self.name}")

    # Accept any int or float (except NaN)
    def validator(self, rule):
        try:
            # Prevent accepting NaN (is valid float but breaks comparison)
            if isnan(float(rule)):
                return False
            else:
                return float(rule)
        except (ValueError, TypeError):
            return False

    # Used for calibration
    def get_raw_reading(self):
        return self.sensor.get_value()

    # Return True if absolute value of current reading exceeds configured threshold
    def condition_met(self):
        if abs(self.sensor.get_value()) > self.current_rule:
            return True
        return False

    # Tares the sensor, surface must not be occupied
    def tare_sensor(self):
        self.sensor.tare()

    # Check condition every second
    async def monitor(self):
        while True:
            print(f"Load cell monitor: {self.sensor.get_value()}")
            new = self.condition_met()

            # If condition changed, overwrite and refresh group
            if new != self.current and new is not None:
                self.current = new
                self.refresh_group()

            await asyncio.sleep(1)
