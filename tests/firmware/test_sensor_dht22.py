import dht
import unittest
from Dht22 import Dht22

# Expected return value of get_attributes method just after instantiation
expected_attributes = {
    "current": None,
    "tolerance": 1.0,
    "current_rule": 74.0,
    "targets": [],
    "scheduled_rule": None,
    "recent_temps": [],
    "name": "sensor1",
    "enabled": True,
    "group": None,
    "units": "fahrenheit",
    "on_threshold": 75.0,
    "nickname": "sensor1",
    "off_threshold": 73.0,
    "rule_queue": [],
    "mode": "cool",
    "_type": "dht22",
    "default_rule": 74
}


class TestDht22(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Create test instance, mock device, mock group
        cls.instance = Dht22("sensor1", "sensor1", "dht22", 74, "cool", 1, "fahrenheit", [], 15)
        cls.instance.set_rule(74)

    def test_01_initial_state(self):
        # Confirm expected attributes just after instantiation
        self.assertIsInstance(self.instance, Dht22)
        self.assertTrue(self.instance.enabled)
        self.assertIsInstance(self.instance.temp_sensor, dht.DHT22)
        self.assertEqual(self.instance.mode, "cool")
        self.assertEqual(self.instance.tolerance, 1)
        self.assertEqual(self.instance.current_rule, 74.0)
        self.assertEqual(self.instance.on_threshold, 75.0)
        self.assertEqual(self.instance.off_threshold, 73.0)
        self.assertEqual(self.instance.recent_temps, [])

    def test_02_get_attributes(self):
        self.maxDiff = None
        attributes = self.instance.get_attributes()
        self.assertEqual(attributes, expected_attributes)

    def test_03_sensor_instance(self):
        # Confirm sensor driver methods return floats
        self.instance.temp_sensor.measure()
        self.assertIsInstance(self.instance.temp_sensor.temperature(), float)
        self.assertIsInstance(self.instance.temp_sensor.humidity(), float)

    def test_04_get_temperature_and_humidity(self):
        # Confirm class methods return floats
        self.assertIsInstance(self.instance.get_temperature(), float)
        self.assertIsInstance(self.instance.get_humidity(), float)

    # Original bug: Some sensors would crash or behave unexpectedly in various situations if
    # default_rule was "enabled" or "disabled". These classes now raise exception in init
    # method to prevent this. Should not be possible to instantiate with invalid default_rule.
    def test_05_regression_invalid_default_rule(self):
        with self.assertRaises(AttributeError):
            Dht22("sensor1", "sensor1", "dht22", "enabled", "cool", 1, "fahrenheit", [], 15)

        with self.assertRaises(AttributeError):
            Dht22("sensor1", "sensor1", "dht22", "disabled", "cool", 1, "fahrenheit", [], 15)
