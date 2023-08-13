import unittest
from machine import SoftI2C
from Group import Group
from Device import Device
from Thermostat import Thermostat

# Expected return value of get_attributes method just after instantiation
expected_attributes = {
    'tolerance': 1.0,
    'nickname': 'sensor1',
    '_type': 'si7021',
    'current': None,
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


# Subclass Group to detect when refresh method called
class MockGroup(Group):
    def __init__(self, name, sensors):
        super().__init__(name, sensors)

        self.refresh_called = False

    def refresh(self, arg=None):
        self.refresh_called = True


class TestThermostat(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Create test instance, mock device, mock group
        cls.target = Device('device1', 'target', 'device', True, '70', '70')
        cls.instance = Thermostat("sensor1", "sensor1", "si7021", 74, "cool", 1, [cls.target])
        cls.group = MockGroup('group1', [cls.instance])
        cls.instance.group = cls.group

        # Dummy send method so group.refresh can run
        def mock_send(state):
            pass
        cls.target.send = mock_send

    def test_01_initial_state(self):
        # Confirm expected attributes just after instantiation
        self.assertIsInstance(self.instance, Thermostat)
        self.assertTrue(self.instance.enabled)
        self.assertIsInstance(self.instance.i2c, SoftI2C)
        self.assertEqual(self.instance.mode, "cool")
        self.assertEqual(self.instance.tolerance, 1)
        self.assertEqual(self.instance.current_rule, 74.0)
        self.assertEqual(self.instance.on_threshold, 75.0)
        self.assertEqual(self.instance.off_threshold, 73.0)
        self.assertEqual(self.instance.recent_temps, [])

    def test_02_get_attributes(self):
        # Confirm expected attributes dict just after instantiation
        attributes = self.instance.get_attributes()
        self.assertEqual(attributes, expected_attributes)

    def test_03_rule_validation_valid(self):
        # Should accept integers and floats between 65 and 90
        self.assertEqual(self.instance.rule_validator(65.0), 65.0)
        self.assertEqual(self.instance.rule_validator(80), 80)
        self.assertEqual(self.instance.rule_validator("72"), 72)
        # Should accept enabled and disabled, case-insensitive
        self.assertEqual(self.instance.rule_validator("Disabled"), "disabled")

    def test_04_rule_validation_invalid(self):
        # Should reject ints and floats less than 65 or greater than 80
        self.assertFalse(self.instance.rule_validator(64))
        self.assertFalse(self.instance.rule_validator(81.0))
        # Should reject all other rule types
        self.assertFalse(self.instance.rule_validator([72]))
        self.assertFalse(self.instance.rule_validator({72: 72}))
        self.assertFalse(self.instance.rule_validator(True))
        self.assertFalse(self.instance.rule_validator(None))
        self.assertFalse(self.instance.rule_validator("string"))

    def test_05_rule_change(self):
        # Starting conditions
        self.assertEqual(self.instance.on_threshold, 75.0)
        self.assertEqual(self.instance.off_threshold, 73.0)

        # Confirm threshold changes when rule changes
        self.assertTrue(self.instance.set_rule(75))
        self.assertEqual(self.instance.current_rule, 75)
        self.assertEqual(self.instance.on_threshold, 76.0)
        self.assertEqual(self.instance.off_threshold, 74.0)

        # Confirm rejects invalid rule
        self.assertFalse(self.instance.set_rule(10))

    def test_06_increment_rule(self):
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

    def test_07_sensor(self):
        # Confirm sensor methods return float
        self.assertIsInstance(self.instance.fahrenheit(), float)
        self.assertIsInstance(self.instance.temp_sensor.temperature, float)
        self.assertIsInstance(self.instance.temp_sensor.relative_humidity, float)

    def test_08_condition_met_cool(self):
        # Set rule to match current temperature, confirm condition is None
        current = self.instance.fahrenheit()
        self.instance.set_rule(current)
        self.assertEqual(self.instance.condition_met(), None)

        # Set rule 2 degrees above current temperature
        # Condition should be False (stop cooling)
        self.instance.set_rule(current + 2)
        self.assertFalse(self.instance.condition_met())

        # Set rule 2 degrees below current temperature
        # Condition should be True (start cooling)
        self.instance.set_rule(current - 2)
        self.assertTrue(self.instance.condition_met())

    def test_09_condition_met_heat(self):
        # Set rule to match current temperature, confirm condition is None
        self.instance.mode = "heat"
        current = self.instance.fahrenheit()
        self.instance.set_rule(current)
        self.assertEqual(self.instance.condition_met(), None)

        # Set rule 2 degrees below current temperature
        # Condition should be False (stop heating)
        self.instance.set_rule(current - 2)
        self.assertFalse(self.instance.condition_met())

        # Set rule 2 degrees above current temperature
        # Condition should be True (start heating)
        self.instance.set_rule(current + 2)
        self.assertTrue(self.instance.condition_met())

    def test_10_condition_met_tolerance(self):
        # Set tolerance to 5 degrees
        self.instance.tolerance = 5
        # Set rule to match current temperature, confirm condition is None
        current = self.instance.fahrenheit()
        self.instance.set_rule(current)
        self.assertEqual(self.instance.condition_met(), None)

        # With tolerance set to 5 degrees, should not turn on OR off at +- 2 degrees
        self.instance.set_rule(current - 2)
        self.assertEqual(self.instance.condition_met(), None)

        self.instance.set_rule(current + 2)
        self.assertEqual(self.instance.condition_met(), None)

        # Set tolerance to 0.1 degrees, set rule to match current temperature
        self.instance.tolerance = 0.1
        current = self.instance.fahrenheit()
        self.assertEqual(self.instance.condition_met(), None)

        # With tolerance set to 0.1 degrees, should turn on/off with very slight temperature change
        self.instance.set_rule(current - 0.2)
        self.assertFalse(self.instance.condition_met())

        self.instance.set_rule(current + 0.2)
        self.assertTrue(self.instance.condition_met())

    def test_11_trigger(self):
        # Should not be able to trigger this sensor type
        self.assertFalse(self.instance.trigger())

    def test_12_audit(self):
        # Ensure Group.refresh not called
        self.group.refresh_called = False

        # Get actual temperature to mock recent changes
        current = self.instance.fahrenheit()

        # Mock temp increasing when heater should NOT be running
        self.instance.mode = 'heat'
        self.instance.set_rule(current - 1)
        self.instance.recent_temps = [current - 4, current - 3, current - 2]
        # Confirm state flips to True (allow heater to turn off), Group.refresh called
        self.instance.audit()
        self.assertTrue(self.target.state)
        self.assertTrue(self.group.refresh_called)

        # Mock temp increasing when air conditioner SHOULD be running
        self.instance.mode = 'cool'
        self.instance.recent_temps = [current - 4, current - 3, current - 2]
        # Confirm state flips to False (allow AC to turn on), Group.refresh called
        self.instance.audit()
        self.assertFalse(self.target.state)
        self.assertTrue(self.group.refresh_called)

        # Mock temp decreasing when air conditioner should NOT be running
        self.instance.set_rule(current + 1)
        self.instance.recent_temps = [current + 4, current + 3, current + 2]
        # Confirm state flips to True (allow AC to turn off), Group.refresh called
        self.instance.audit()
        self.assertTrue(self.target.state)
        self.assertTrue(self.group.refresh_called)

        # Mock temp decreasing when heater SHOULD be running
        self.instance.mode = 'heat'
        self.instance.recent_temps = [current + 4, current + 3, current + 2]
        # Confirm state flips to True (allow heater to turn on), Group.refresh called
        self.instance.audit()
        self.assertFalse(self.target.state)
        self.assertTrue(self.group.refresh_called)

    def test_13_add_routines(self):
        # Confirm no routines in group, instance.recent_temps not empty
        self.assertEqual(len(self.instance.group.post_action_routines), 0)
        self.instance.recent_temps = [69, 70, 71]

        # Call method, confirm routine added
        self.instance.add_routines()
        self.assertEqual(len(self.instance.group.post_action_routines), 1)

        # Run routine, confirm recent temps cleared
        self.instance.group.post_action_routines[0]()
        self.assertEqual(len(self.instance.recent_temps), 0)

    def test_14_instantiate_with_all_modes(self):
        # Instantiate in heat mode
        test = Thermostat("sensor1", "sensor1", "si7021", 74, "heat", 1, [])
        self.assertEqual(test.mode, "heat")

        # Instantiate in cool mode
        test = Thermostat("sensor1", "sensor1", "si7021", 74, "cool", 1, [])
        self.assertEqual(test.mode, "cool")

        # Instantiate with unsupported mode
        with self.assertRaises(ValueError):
            Thermostat("sensor1", "sensor1", "si7021", 74, "invalid", 1, [])

    # Original bug: Some sensors would crash or behave unexpectedly if default_rule was "enabled" or "disabled"
    # in various situations. These classes now raise exception in init method to prevent this.
    # It should no longer be possible to instantiate with invalid default_rule.
    def test_15_regression_invalid_default_rule(self):
        with self.assertRaises(AttributeError):
            Thermostat("sensor1", "sensor1", "si7021", "enabled", "cool", 1, [])

        with self.assertRaises(AttributeError):
            Thermostat("sensor1", "sensor1", "si7021", "disabled", "cool", 1, [])

    # Original bug: increment_rule cast argument to float inside try/except, relying
    # on exception to detect invalid argument. Since NaN is a valid float no exception
    # was raised and set_rule was called with NaN. The validator correctly rejected NaN
    # but with an ambiguous error. NaN is now rejected directly by increment_rule.
    def test_16_regression_increment_by_nan(self):
        # Starting condition
        self.instance.set_rule(70)

        # Attempt to increment by NaN, confirm error, confirm rule does not change
        response = self.instance.increment_rule("NaN")
        self.assertEqual(response, {'ERROR': 'Invalid argument nan'})
        self.assertEqual(self.instance.current_rule, 70.0)

    # Original bug: get_threshold was called by set_rule method, but enable method set
    # current_rule directly without calling set_rule. This could result in inaccurate
    # thresholds, effectively ignoring the current_rule.
    def test_17_regression_fail_to_update_thresholds(self):
        # Confirm initial thresholds
        self.instance.tolerance = 1.0
        self.instance.set_rule(70)
        self.assertEqual(self.instance.on_threshold, 69.0)
        self.assertEqual(self.instance.off_threshold, 71.0)

        # Set scheduled rule different than current (requires new thresholds)
        self.instance.scheduled_rule = 75

        # Set rule to disabled, re-enable, scheduled_rule should take effect
        self.instance.set_rule('disabled')
        self.instance.enable()
        self.assertEqual(self.instance.current_rule, 75.0)

        # Confirm thresholds updated correctly
        self.assertEqual(self.instance.on_threshold, 74.0)
        self.assertEqual(self.instance.off_threshold, 76.0)

    # Original bug: Enable method handled current_rule == 'disabled' by arbitrarily setting
    # scheduled_rule as current_rule with no validation. This made it possible for a string
    # representation of float to be set as current_rule, raising exception when get_threshold
    # method called. Now uses set_rule method to cast rule to required type.
    def test_18_regression_enable_sets_string_rule(self):
        # Set scheduled_rule to string representation of int
        self.instance.scheduled_rule = '70.0'

        # Set rule to disabled to trigger first conditional in enable method
        self.instance.set_rule('disabled')
        self.assertEqual(self.instance.current_rule, 'disabled')

        # Enable, should fall back to scheduled_rule and cast to int
        self.instance.enable()
        self.assertEqual(self.instance.current_rule, 70.0)

        # Call get_threshold method, should not crash
        self.instance.get_threshold()
