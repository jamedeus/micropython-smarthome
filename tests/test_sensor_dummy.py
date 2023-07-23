import unittest
from Dummy import Dummy

# Expected return value of get_attributes method just after instantiation
expected_attributes = {
    'rule_queue': [],
    'enabled': True,
    'default_rule': 'on',
    'name': 'sensor1',
    '_type': 'dummy',
    'nickname': 'sensor1',
    'current_rule': None,
    'scheduled_rule': None,
    'targets': []
}


class TestDummySensor(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.instance = Dummy("sensor1", "sensor1", "dummy", "on", [])

    def test_01_initial_state(self):
        self.assertIsInstance(self.instance, Dummy)
        self.assertTrue(self.instance.enabled)

    def test_02_get_attributes(self):
        attributes = self.instance.get_attributes()
        self.assertEqual(attributes, expected_attributes)

    def test_03_rule_validation_valid(self):
        # Should accept on and off in addition to enabled and disabled, all case insensitive
        self.assertEqual(self.instance.rule_validator("on"), "on")
        self.assertEqual(self.instance.rule_validator("On"), "on")
        self.assertEqual(self.instance.rule_validator("ON"), "on")
        self.assertEqual(self.instance.rule_validator("off"), "off")
        self.assertEqual(self.instance.rule_validator("Disabled"), "disabled")
        self.assertEqual(self.instance.rule_validator("DISABLED"), "disabled")
        self.assertEqual(self.instance.rule_validator("Enabled"), "enabled")
        self.assertEqual(self.instance.rule_validator("enabled"), "enabled")

    def test_04_rule_validation_invalid(self):
        # Should reject all other strings, non-strings
        self.assertFalse(self.instance.rule_validator(True))
        self.assertFalse(self.instance.rule_validator(None))
        self.assertFalse(self.instance.rule_validator("string"))
        self.assertFalse(self.instance.rule_validator(42))
        self.assertFalse(self.instance.rule_validator(["on"]))
        self.assertFalse(self.instance.rule_validator({"on": "on"}))

    def test_05_rule_change(self):
        # Should accept on and off
        self.assertTrue(self.instance.set_rule("off"))
        self.assertEqual(self.instance.current_rule, 'off')
        self.assertTrue(self.instance.set_rule("on"))
        self.assertEqual(self.instance.current_rule, 'on')

    def test_06_condition_met(self):
        # Should always return True when rule is on
        self.instance.set_rule("on")
        self.assertTrue(self.instance.condition_met())

        # Should always return False when rule is off
        self.instance.set_rule("off")
        self.assertFalse(self.instance.condition_met())

        # Should always return None when rule is neither on nor off
        self.instance.set_rule("Disabled")
        self.assertEqual(self.instance.condition_met(), None)

    def test_07_trigger(self):
        # Ensure current rule is off to avoid false positive
        self.instance.set_rule("off")
        self.assertFalse(self.instance.condition_met())
        # Trigger, condition should now be met, current_rule should be on
        self.assertTrue(self.instance.trigger())
        self.assertTrue(self.instance.condition_met())
        self.assertEqual(self.instance.current_rule, "on")

    # Original bug: Some sensors would crash or behave unexpectedly if default_rule was "enabled" or "disabled"
    # in various situations. These classes now raise exception in init method to prevent this.
    # It should no longer be possible to instantiate with invalid default_rule.
    def test_08_regression_invalid_default_rule(self):
        # assertRaises fails for some reason, this approach seems reliable
        try:
            Dummy("sensor1", "sensor1", "dummy", "disabled", [])
            # Should not make it to this line, test failed
            self.assertFalse(True)
        except AttributeError:
            # Should raise exception, test passed
            self.assertTrue(True)

        try:
            Dummy("sensor1", "sensor1", "dummy", "enabled", [])
            # Should not make it to this line, test failed
            self.assertFalse(True)
        except AttributeError:
            # Should raise exception, test passed
            self.assertTrue(True)
