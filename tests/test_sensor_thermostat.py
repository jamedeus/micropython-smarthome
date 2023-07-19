import unittest
from Group import Group
from Device import Device
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
    'group': 'group1',
    'mode': 'cool',
    'targets': ['device1'],
    'rule_queue': [],
    'name': 'sensor1',
    'on_threshold': 75.0,
    'off_threshold': 73.0,
    'recent_temps': []
}


class TestThermostat(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Create test instance, mock device, mock group
        cls.target = Device('device1', 'target', 'device', True, '70', '70')
        cls.instance = Thermostat("sensor1", "sensor1", "si7021", 74, "cool", 1, [cls.target])
        group = Group('group1', [cls.instance])
        cls.instance.group = group

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

    def test_14_increment_rule(self):
        # Set rule to 70, increment by 1, confirm rule is now 71
        self.instance.current_rule = 70
        self.assertTrue(self.instance.increment_rule(1))
        self.assertEqual(self.instance.current_rule, 71)

        # Set rule to disabled, confirm correct error
        self.instance.set_rule('Disabled')
        self.assertEqual(
            self.instance.increment_rule(1),
            {"ERROR": "Unable to increment current rule (disabled)"}
        )

    def test_15_audit(self):
        # Get actual temperature to mock recent changes
        current = self.instance.fahrenheit()

        # Mock temp increasing when heater should NOT be running
        self.instance.mode = 'heat'
        self.instance.set_rule(current - 1)
        self.instance.recent_temps = [current - 4, current - 3, current - 2]
        self.instance.audit()
        # Confirm state flips to True, allows loop to turn heater off
        self.assertTrue(self.target.state)

        # Mock temp increasing when air conditioner SHOULD be running
        self.instance.mode = 'cool'
        self.instance.recent_temps = [current - 4, current - 3, current - 2]
        self.instance.audit()
        # Confirm state flips to False, allows loop to turn AC on
        self.assertFalse(self.target.state)

        # Mock temp decreasing when air conditioner should NOT be running
        self.instance.set_rule(current + 1)
        self.instance.recent_temps = [current + 4, current + 3, current + 2]
        self.instance.audit()
        # Confirm state flips to True, allows loop to turn AC off
        self.assertTrue(self.target.state)

        # Mock temp decreasing when heater SHOULD be running
        self.instance.mode = 'heat'
        self.instance.recent_temps = [current + 4, current + 3, current + 2]
        self.instance.audit()
        # Confirm state flips to False, allows loop to turn heater on
        self.assertFalse(self.target.state)

    def test_16_instantiate_with_all_modes(self):
        # Instantiate in heat mode
        test = Thermostat("sensor1", "sensor1", "si7021", 74, "heat", 1, [])
        self.assertEqual(test.mode, "heat")

        # Instantiate in cool mode
        test = Thermostat("sensor1", "sensor1", "si7021", 74, "cool", 1, [])
        self.assertEqual(test.mode, "cool")

        # Instantiate with unsupported mode
        try:
            Thermostat("sensor1", "sensor1", "si7021", 74, "invalid", 1, [])
            # Should not make it to this line, test failed
            self.assertFalse(True)
        except ValueError:
            # Should raise exception, test passed
            self.assertTrue(True)

    # Original bug: Some sensors would crash or behave unexpectedly if default_rule was "enabled" or "disabled"
    # in various situations. These classes now raise exception in init method to prevent this.
    # It should no longer be possible to instantiate with invalid default_rule.
    def test_17_regression_invalid_default_rule(self):
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
