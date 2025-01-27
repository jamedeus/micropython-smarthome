import si7021
from machine import Pin, SoftI2C
from Thermostat import Thermostat


class Si7021(Thermostat):
    '''Driver for SI7021 temperature and humidity sensor used as a thermostat.
    Turns target devices on and off when configurable temperature thresholds
    are crossed. The SI7021 must be connected to ESP32 via I2C (SDA = GPIO21,
    SCL = GPIO22).

    Args:
      name:         Unique, sequential config name (device1, device2, etc)
      nickname:     User-configured friendly name shown on frontend
      _type:        Instance type, determines driver class and frontend UI
      enabled:      Initial enable state (True or False)
      default_rule: Fallback rule used when no other valid rules are available
      schedule:     Dict with timestamps/keywords as keys, rules as values
      mode:         Must be "cool" (turn on when temperature > current_rule) or
                    "heat" (turn on when temperature < current_rule)
      tolerance:    Number between 0.1 and 10, determines buffer above and
                    below current_rule where devices are not turned on or off
      units:        Must be "celsius", "fahrenheit", or "kelvin"
      targets:      List of device names (device1 etc) controlled by sensor

    On and off temperature thresholds are calculated by adding and subtracting
    the tolerance attribute from current_rule. If mode is heat target devices
    will turn on when current temperature is less than the lower threshold, and
    turn off when temperature is greater than the higher threshold. If mode is
    cool this is reversed.

    Example: If current_rule is 20 and tolerance is 2 the thresholds will be 18
    and 22. In cool mode devices will turn on when temperature exceeds 22, and
    turn off when temperature drops below 18. In heat mode devices will turn on
    when temperature drops below 18, and turn off when temperature exceeds 22.

    Supports universal rules ("enabled" and "disabled") and temperature cutoff
    rules (float between 18 and 27 celsius or equivalent in configured units).
    The default_rule must be a float (not universal rule).
    '''

    def __init__(self, name, nickname, _type, default_rule, schedule, mode, tolerance, units, targets):
        # Setup I2C interface
        self.i2c = SoftI2C(Pin(22), Pin(21))
        self.temp_sensor = si7021.Si7021(self.i2c)

        # Set mode, tolerance, units, current_rule, create monitor task
        super().__init__(name, nickname, _type, default_rule, schedule, mode, tolerance, units, targets)
        self.log.info("Instantiated, units=%s, tolerance=%s", units, tolerance)

    def get_raw_temperature(self):
        '''Returns raw temperature reading in Celsius. Called by parent class
        get_temperature method (returns reading converted to configured units).
        '''
        return self.temp_sensor.temperature

    def get_humidity(self):
        '''Returns current relative humidity reading (percentage).'''

        return self.temp_sensor.relative_humidity

    def get_attributes(self):
        '''Return JSON-serializable dict containing all current attributes
        Called by API get_attributes endpoint, more verbose than status
        '''
        attributes = super().get_attributes()
        # Remove non-serializable objects
        del attributes["i2c"]
        del attributes["temp_sensor"]
        return attributes
