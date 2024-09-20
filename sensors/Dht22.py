import dht
import logging
from machine import Pin
from Thermostat import Thermostat


class Dht22(Thermostat):
    '''Driver for Dht22 temperature and humidity sensor used as a thermostat.
    Turns target devices on and off when configurable temperature thresholds
    are crossed.

    Args:
      name:         Unique, sequential config name (device1, device2, etc)
      nickname:     User-configured friendly name shown on frontend
      _type:        Instance type, determines driver class and frontend UI
      enabled:      Initial enable state (True or False)
      default_rule: Fallback rule used when no other valid rules are available
      mode:         Must be "cool" (turn on when temperature > current_rule) or
                    "heat" (turn on when temperature < current_rule)
      tolerance:    Number between 0.1 and 10, determines buffer above and
                    below current_rule where devices are not turned on or off
      units:        Must be "celsius", "fahrenheit", or "kelvin"
      targets:      List of device names (device1 etc) controlled by sensor
      pin:          The ESP32 pin connected to the DHT22 data pin

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

    def __init__(self, name, nickname, _type, default_rule, mode, tolerance, units, targets, pin):
        # Instantiate pin and sensor driver
        self.temp_sensor = dht.DHT22(Pin(int(pin)))

        # Set mode, tolerance, units, current_rule, create monitor task
        super().__init__(name, nickname, _type, default_rule, mode, tolerance, units, targets)
        self.log.info(
            "Instantiated Dht22 named %s, units=%s, tolerance=%s",
            self.name, self.units, self.tolerance
        )

        # Set name for module's log lines
        self.log = logging.getLogger("Dht22")

    def get_raw_temperature(self):
        '''Returns raw temperature reading in Celsius. Called by parent class
        get_temperature method (returns reading converted to configured units).
        '''
        self.temp_sensor.measure()
        return self.temp_sensor.temperature()

    def get_humidity(self):
        '''Returns current relative humidity reading (percentage).'''

        self.temp_sensor.measure()
        return self.temp_sensor.humidity()

    def get_attributes(self):
        '''Return JSON-serializable dict containing all current attributes
        Called by API get_attributes endpoint, more verbose than status
        '''
        attributes = super().get_attributes()
        # Remove non-serializable object
        del attributes["temp_sensor"]
        return attributes
