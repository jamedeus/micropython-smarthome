import asyncio
import logging
from math import isnan
from machine import Pin
from hx711 import HX711
from Sensor import Sensor

# Set name for module's log lines
log = logging.getLogger("Load_Cell")


class LoadCell(Sensor):
    '''Driver for HX711 chip connected to load cell, used as a pressure sensor.
    Turns target devices on when load cell value is greater than current_rule,
    turns devices off when load cell value is less than current_rule. Can be
    used to detect if a chair/couch/bed etc is occupied.

    Args:
      name:         Unique, sequential config name (sensor1, sensor2, etc)
      nickname:     User-configured friendly name shown on frontend
      _type:        Instance type, determines driver class and frontend UI
      enabled:      Initial enable state (True or False)
      current_rule: Initial rule, has different effects depending on subclass
      default_rule: Fallback rule used when no other valid rules are available
      targets:      List of device names (device1 etc) controlled by sensor
      pin_data:     The ESP32 pin connected to the HX711 data pin
      pin_clock:    The ESP32 pin connected to the HX711 clock pin

    Supports universal rules ("enabled" and "disabled") and integers or floats
    (load cell reading threshold when the sensor is activated).
    The default_rule must be an integer or float (not universal rule).
    '''

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

        log.info("Instantiated load cell sensor named %s", self.name)

    def validator(self, rule):
        '''Accepts any valid integer or float except NaN.'''

        try:
            # Prevent incorrectly accepting True and False (last condition
            # casts to 1.0, 0.0 respectively)
            if isinstance(rule, bool):
                return False
            # Prevent accepting NaN (is valid float but breaks comparison)
            elif isnan(float(rule)):
                return False
            else:
                return float(rule)
        except (ValueError, TypeError):
            return False

    def get_raw_reading(self):
        '''Returns raw reading from load cell sensor, used to calibrate on/off
        threshold. Called by load_cell_read API endpoint.
        '''

        return self.sensor.get_value()

    def condition_met(self):
        '''Returns True if absolute value of current load cell reading exceeds
        current_rule threshold, otherwise False.
        '''
        if abs(self.sensor.get_value()) > self.current_rule:
            return True
        return False

    def tare_sensor(self):
        '''Tares the sensor (surface must not be occupied).
        Called by load_cell_tare API endpoint.
        '''

        self.sensor.tare()

    async def monitor(self):
        '''Async coroutine, checks load cell condition every second. Turns
        target devices on or off when condition changes.
        '''
        while True:
            self.print(f"Load cell monitor: {self.sensor.get_value()}")
            new = self.condition_met()

            # If condition changed, overwrite and refresh group
            if new != self.current and new is not None:
                self.current = new
                self.refresh_group()

            await asyncio.sleep(1)

    def get_attributes(self):
        '''Return JSON-serializable dict containing all current attributes
        Called by API get_attributes endpoint, more verbose than status
        '''
        attributes = super().get_attributes()
        # Remove non-serializable object
        del attributes["sensor"]
        return attributes
