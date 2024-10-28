import asyncio
from math import isnan
from machine import Pin
from hx711 import HX711
from SensorWithLoop import SensorWithLoop


class LoadCell(SensorWithLoop):
    '''Driver for HX711 chip connected to load cell, used as a pressure sensor.
    Turns target devices on when load cell value is greater than current_rule,
    turns devices off when load cell value is less than current_rule. Can be
    used to detect if a chair/couch/bed etc is occupied.

    Args:
      name:         Unique, sequential config name (sensor1, sensor2, etc)
      nickname:     User-configured friendly name shown on frontend
      _type:        Instance type, determines driver class and frontend UI
      enabled:      Initial enable state (True or False)
      default_rule: Fallback rule used when no other valid rules are available
      targets:      List of device names (device1 etc) controlled by sensor
      pin_data:     The ESP32 pin connected to the HX711 data pin
      pin_clock:    The ESP32 pin connected to the HX711 clock pin

    Supports universal rules ("enabled" and "disabled") and integers or floats
    (load cell reading threshold when the sensor is activated).
    The default_rule must be an integer or float (not universal rule).
    '''

    def __init__(self, name, nickname, _type, default_rule, schedule, targets, pin_data, pin_clock):
        super().__init__(name, nickname, _type, True, default_rule, schedule, targets)

        # Instantiate sensor, tare
        data = Pin(int(pin_data), Pin.IN, Pin.PULL_DOWN)
        clock = Pin(int(pin_clock), Pin.OUT)
        self.sensor = HX711(clock, data)
        self.tare_sensor()

        # Track output of condition_met (set by monitor callback)
        self.current = None

        # Start monitor loop (checks if threshold met every second)
        self.monitor_task = asyncio.create_task(self.monitor())

        self.log.info(
            "Instantiated, pin_data=%s, pin_clock=%s",
            pin_data, pin_clock
        )

    def validator(self, rule):
        '''Accepts any valid integer or float except NaN.'''

        try:
            # Prevent incorrectly accepting True and False (last condition
            # casts to 1.0, 0.0 respectively)
            if isinstance(rule, bool):
                return False
            # Prevent accepting NaN (is valid float but breaks comparison)
            if isnan(float(rule)):
                return False
            # Rule valid if able to cast to float
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
        try:
            if abs(self.sensor.get_value()) > self.current_rule:
                return True
            return False
        except TypeError:
            # Current rule is not int (sensor disabled)
            return False

    def tare_sensor(self):
        '''Tares the sensor (surface must not be occupied).
        Called by load_cell_tare API endpoint.
        '''
        self.log.debug("tare_sensor method called")
        self.sensor.tare()

    async def monitor(self):
        '''Async coroutine, checks load cell condition every second. Turns
        target devices on or off when condition changes.
        '''
        self.log.debug("Starting LoadCell.monitor coro")
        try:
            while True:
                self.log.debug("sensor value: %s", self.get_raw_reading())
                new = self.condition_met()

                # If condition changed, overwrite and refresh group
                if new != self.current and new is not None:
                    self.log.debug(
                        "monitor: condition changed from %s to %s",
                        self.current, new
                    )
                    self.current = new
                    self.refresh_group()

                # Poll every second
                await asyncio.sleep(1)

        # Sensor disabled, exit loop
        except asyncio.CancelledError:
            self.log.debug("Exiting LoadCell.monitor coro")
            return False

    def get_attributes(self):
        '''Return JSON-serializable dict containing all current attributes
        Called by API get_attributes endpoint, more verbose than status
        '''
        attributes = super().get_attributes()
        # Remove non-serializable object
        del attributes["sensor"]
        return attributes
