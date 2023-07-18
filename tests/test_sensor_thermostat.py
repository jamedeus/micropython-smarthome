import unittest
from Thermostat import Thermostat

# Expected return value of get_attributes method just after instantiation
expected_attributes = {
    'tolerance': 1.0,
    'nickname': 'sensor1',
    '_type': 'si7021',
    'current_rule': 74.0,
    'scheduled_rule': 74,
    'default_rule': 74,
    'enabled': True,
    'mode': 'cool',
    'targets': [],
    'rule_queue': [],
    'name': 'sensor1',
    'on_threshold': 75.0,
    'off_threshold': 73.0,
    'recent_temps': []
}


class TestThermostat(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.instance = Thermostat("sensor1", "sensor1", "si7021", 74, "cool", 1, [])

    def test_01_initial_state(self):
        self.assertIsInstance(self.instance, Thermostat)
        self.assertTrue(self.instance.enabled)

    def test_02_get_attributes(self):
        attributes = self.instance.get_attributes()
        self.assertEqual(attributes, expected_attributes)

    def test_03_rule_validation_valid(self):
        self.assertEqual(self.instance.rule_validator(65), 65)
        self.assertEqual(self.instance.rule_validator(80), 80)
        self.assertEqual(self.instance.rule_validator("72"), 72)
        self.assertEqual(self.instance.rule_validator("Disabled"), "disabled")

    def test_04_rule_validation_invalid(self):
        self.assertFalse(self.instance.rule_validator(64))
        self.assertFalse(self.instance.rule_validator(81))
        self.assertFalse(self.instance.rule_validator([72]))
        self.assertFalse(self.instance.rule_validator({72: 72}))
        self.assertFalse(self.instance.rule_validator(True))
        self.assertFalse(self.instance.rule_validator(None))
        self.assertFalse(self.instance.rule_validator("string"))

    def test_05_rule_change(self):
        self.assertTrue(self.instance.set_rule(75))
        self.assertEqual(self.instance.current_rule, 75)

    def test_06_enable_disable(self):
        self.instance.disable()
        self.assertFalse(self.instance.enabled)
        self.instance.enable()
        self.assertTrue(self.instance.enabled)

    def test_07_disable_by_rule_change(self):
        self.instance.set_rule("Disabled")
        self.assertFalse(self.instance.enabled)

    def test_08_enable_by_rule_change(self):
        self.instance.set_rule(70)
        self.assertTrue(self.instance.enabled)

    def test_09_sensor(self):
        self.assertIsInstance(self.instance.fahrenheit(), float)
        self.assertIsInstance(self.instance.temp_sensor.temperature, float)
        self.assertIsInstance(self.instance.temp_sensor.relative_humidity, float)

    def test_10_condition_met(self):
        current = self.instance.fahrenheit()

        self.instance.set_rule(current)
        self.assertEqual(self.instance.condition_met(), None)

        self.instance.set_rule(current + 2)
        self.assertFalse(self.instance.condition_met())

        self.instance.set_rule(current - 2)
        self.assertTrue(self.instance.condition_met())

    def test_11_condition_met_heat(self):
        self.instance.mode = "heat"
        self.instance.get_threshold()
        current = self.instance.fahrenheit()

        self.instance.set_rule(current)
        self.assertEqual(self.instance.condition_met(), None)

        self.instance.set_rule(current - 2)
        self.assertFalse(self.instance.condition_met())

        self.instance.set_rule(current + 2)
        self.assertTrue(self.instance.condition_met())

    def test_12_condition_met_tolerance(self):
        self.instance.mode = "heat"
        self.instance.tolerance = 5
        current = self.instance.fahrenheit()

        self.instance.set_rule(current)
        self.assertEqual(self.instance.condition_met(), None)

        # With tolerance set to 5 degrees, should not turn on OR off at +- 2 degrees
        self.instance.set_rule(current - 2)
        self.assertEqual(self.instance.condition_met(), None)

        self.instance.set_rule(current + 2)
        self.assertEqual(self.instance.condition_met(), None)

        self.instance.tolerance = 0.1
        current = self.instance.fahrenheit()

        # With tolerance set to 0.1 degrees, should turn on/off with very slight temperature change
        self.instance.set_rule(current - 0.2)
        self.assertFalse(self.instance.condition_met())

        self.instance.set_rule(current + 0.2)
        self.assertTrue(self.instance.condition_met())

    def test_13_trigger(self):
        # Should not be able to trigger this sensor type
        self.assertFalse(self.instance.trigger())

    # Original bug: Some sensors would crash or behave unexpectedly if default_rule was "enabled" or "disabled"
    # in various situations. These classes now raise exception in init method to prevent this.
    # It should no longer be possible to instantiate with invalid default_rule.
    def test_14_regression_invalid_default_rule(self):
        # assertRaises fails for some reason, this approach seems reliable
        try:
            Thermostat("sensor1", "sensor1", "si7021", "enabled", "cool", 1, [])
            # Should not make it to this line, test failed
            self.assertFalse(True)
        except AttributeError:
            # Should raise exception, test passed
            self.assertTrue(True)

        try:
            Thermostat("sensor1", "sensor1", "si7021", "disabled", "cool", 1, [])
            # Should not make it to this line, test failed
            self.assertFalse(True)
        except AttributeError:
            # Should raise exception, test passed
            self.assertTrue(True)
