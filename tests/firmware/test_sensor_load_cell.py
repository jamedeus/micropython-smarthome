import unittest
from Group import Group
from LoadCell import LoadCell

# Expected return value of get_attributes method just after instantiation
expected_attributes = {
    'rule_queue': [],
    'enabled': True,
    'group': 'group1',
    'default_rule': '100000',
    'name': 'sensor1',
    '_type': 'load-cell',
    'nickname': 'sensor1',
    'current': None,
    'current_rule': None,
    'scheduled_rule': None,
    'targets': []
}


# Subclass Group to detect when refresh method called
class MockGroup(Group):
    def __init__(self, name, sensors):
        super().__init__(name, sensors)

        self.refresh_called = False

    def refresh(self, arg=None):
        self.refresh_called = True
        super().refresh()


class TestLoadCellSensor(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.instance = LoadCell("sensor1", "sensor1", "load-cell", "100000", [], 18, 19)
        cls.group = MockGroup("group1", [cls.instance])
        cls.instance.group = cls.group

    def test_01_initial_state(self):
        self.assertIsInstance(self.instance, LoadCell)
        self.assertTrue(self.instance.enabled)

    def test_02_get_attributes(self):
        attributes = self.instance.get_attributes()
        self.assertEqual(attributes, expected_attributes)

    def test_03_rule_validation_valid(self):
        # Should accept integer in addition to enabled and disabled, all case insensitive
        self.assertEqual(self.instance.rule_validator("100000"), 100000)
        self.assertEqual(self.instance.rule_validator(100000), 100000)
        self.assertEqual(self.instance.rule_validator("Disabled"), "disabled")
        self.assertEqual(self.instance.rule_validator("DISABLED"), "disabled")
        self.assertEqual(self.instance.rule_validator("Enabled"), "enabled")
        self.assertEqual(self.instance.rule_validator("enabled"), "enabled")

    def test_04_rule_validation_invalid(self):
        # Should reject non-integer types
        self.assertFalse(self.instance.rule_validator("string"))
        self.assertFalse(self.instance.rule_validator([100000]))
        self.assertFalse(self.instance.rule_validator({"rule": "100000"}))
        self.assertFalse(self.instance.rule_validator(float('NaN')))

    def test_05_condition_met(self):
        # Get raw reading
        current = self.instance.get_raw_reading()

        # Set rule significantly lower than reading, should return True
        self.instance.set_rule(current - 10000)
        self.assertTrue(self.instance.condition_met())

        # Set rule significantly higher than reading, should return False
        self.instance.set_rule(current + 10000)
        self.assertFalse(self.instance.condition_met())

    def test_06_trigger(self):
        # Should not be able to trigger this sensor type
        self.assertFalse(self.instance.trigger())

    # Original bug: validator cast rule to float and only rejected if an
    # exception was raised. If the validator received True or False it would
    # cast to 1.0 or 0.0 respectively and accept incorrectly.
    def test_07_regression_validator_excepts_bool(self):
        self.assertFalse(self.instance.rule_validator(True))
        self.assertFalse(self.instance.rule_validator(False))
