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
        self.assertEqual(self.instance.rule_validator("on"), "on")
        self.assertEqual(self.instance.rule_validator("On"), "on")
        self.assertEqual(self.instance.rule_validator("ON"), "on")
        self.assertEqual(self.instance.rule_validator("off"), "off")
        self.assertEqual(self.instance.rule_validator("Disabled"), "disabled")
        self.assertEqual(self.instance.rule_validator("DISABLED"), "disabled")
        self.assertEqual(self.instance.rule_validator("Enabled"), "enabled")
        self.assertEqual(self.instance.rule_validator("enabled"), "enabled")

    def test_04_rule_validation_invalid(self):
        self.assertFalse(self.instance.rule_validator(True))
        self.assertFalse(self.instance.rule_validator(None))
        self.assertFalse(self.instance.rule_validator("string"))
        self.assertFalse(self.instance.rule_validator(42))
        self.assertFalse(self.instance.rule_validator(["on"]))
        self.assertFalse(self.instance.rule_validator({"on": "on"}))

    def test_05_rule_change(self):
        self.assertTrue(self.instance.set_rule("off"))
        self.assertEqual(self.instance.current_rule, 'off')
        self.assertTrue(self.instance.set_rule("on"))
        self.assertEqual(self.instance.current_rule, 'on')

    def test_06_enable_disable(self):
        self.instance.disable()
        self.assertFalse(self.instance.enabled)
        self.instance.enable()
        self.assertTrue(self.instance.enabled)

    def test_07_disable_by_rule_change(self):
        self.instance.set_rule("Disabled")
        self.assertFalse(self.instance.enabled)

    def test_08_enable_by_rule_change(self):
        self.instance.set_rule("enabled")
        self.assertTrue(self.instance.enabled)
        self.assertEqual(self.instance.current_rule, "on")

    def test_09_condition_met(self):
        self.instance.set_rule("on")
        self.assertTrue(self.instance.condition_met())

        self.instance.set_rule("off")
        self.assertFalse(self.instance.condition_met())

        self.instance.set_rule("Disabled")
        self.assertEqual(self.instance.condition_met(), None)

    def test_10_trigger(self):
        # Ensure current rule is off to avoid false positive
        self.instance.set_rule("off")
        self.assertFalse(self.instance.condition_met())
        # Trigger, condition should now be met
        self.assertTrue(self.instance.trigger())
        self.assertTrue(self.instance.condition_met())

    # Original bug: Some sensors would crash or behave unexpectedly if default_rule was "enabled" or "disabled"
    # in various situations. These classes now raise exception in init method to prevent this.
    # It should no longer be possible to instantiate with invalid default_rule.
    def test_11_regression_invalid_default_rule(self):
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
