import si7021
import unittest
from machine import SoftI2C
from Si7021 import Si7021


class TestThermostat(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Create test instance
        cls.instance = Si7021("sensor1", "sensor1", "si7021", 74, "cool", 1, "fahrenheit", [])

    def test_01_initial_state(self):
        # Confirm expected attributes just after instantiation
        self.assertIsInstance(self.instance, Si7021)
        self.assertTrue(self.instance.enabled)
        self.assertIsInstance(self.instance.temp_sensor, si7021.Si7021)
        self.assertIsInstance(self.instance.i2c, SoftI2C)
        self.assertEqual(self.instance.mode, "cool")
        self.assertEqual(self.instance.tolerance, 1)
        self.assertEqual(self.instance.current_rule, 74.0)
        self.assertEqual(self.instance.on_threshold, 75.0)
        self.assertEqual(self.instance.off_threshold, 73.0)
        self.assertEqual(self.instance.recent_temps, [])

    def test_02_sensor_instance(self):
        # Confirm sensor driver methods return floats
        self.assertIsInstance(self.instance.temp_sensor.temperature, float)
        self.assertIsInstance(self.instance.temp_sensor.relative_humidity, float)

    def test_03_get_temperature_and_humidity(self):
        # Confirm class methods return floats
        self.assertIsInstance(self.instance.get_temperature(), float)
        self.assertIsInstance(self.instance.get_humidity(), float)

    # Original bug: Some sensors would crash or behave unexpectedly in various situations if
    # default_rule was "enabled" or "disabled". These classes now raise exception in init
    # method to prevent this. Should not be possible to instantiate with invalid default_rule.
    def test_04_regression_invalid_default_rule(self):
        with self.assertRaises(AttributeError):
            Si7021("sensor1", "sensor1", "si7021", "enabled", "cool", 1, "fahrenheit", [])

        with self.assertRaises(AttributeError):
            Si7021("sensor1", "sensor1", "si7021", "disabled", "cool", 1, "fahrenheit", [])
