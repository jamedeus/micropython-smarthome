import unittest
from Dummy import Dummy



class TestDummySensor(unittest.TestCase):

    def __dir__(self):
        return ["test_instantiation", "test_rule_validation_valid", "test_rule_validation_invalid", "test_rule_change", "test_enable_disable", "test_disable_by_rule_change", "test_enable_by_rule_change", "test_condition_met", "test_trigger", "test_regression_invalid_default_rule"]

    def test_instantiation(self):
        self.instance = Dummy("sensor1", "sensor1", "dummy", True, None, "on", [])
        self.assertIsInstance(self.instance, Dummy)
        self.assertTrue(self.instance.enabled)

    def test_rule_validation_valid(self):
        self.assertIs(self.instance.rule_validator("on"), "on")
        self.assertIs(self.instance.rule_validator("On"), "on")
        self.assertIs(self.instance.rule_validator("ON"), "on")
        self.assertIs(self.instance.rule_validator("off"), "off")
        self.assertIs(self.instance.rule_validator("Disabled"), "disabled")
        self.assertIs(self.instance.rule_validator("DISABLED"), "disabled")
        self.assertIs(self.instance.rule_validator("Enabled"), "enabled")
        self.assertIs(self.instance.rule_validator("enabled"), "enabled")

    def test_rule_validation_invalid(self):
        self.assertFalse(self.instance.rule_validator(True))
        self.assertFalse(self.instance.rule_validator(None))
        self.assertFalse(self.instance.rule_validator("string"))
        self.assertFalse(self.instance.rule_validator(42))
        self.assertFalse(self.instance.rule_validator(["on"]))
        self.assertFalse(self.instance.rule_validator({"on":"on"}))

    def test_rule_change(self):
        self.assertTrue(self.instance.set_rule("off"))
        self.assertEqual(self.instance.current_rule, 'off')
        self.assertTrue(self.instance.set_rule("on"))
        self.assertEqual(self.instance.current_rule, 'on')

    def test_enable_disable(self):
        self.instance.disable()
        self.assertFalse(self.instance.enabled)
        self.instance.enable()
        self.assertTrue(self.instance.enabled)

    def test_disable_by_rule_change(self):
        self.instance.set_rule("Disabled")
        self.assertFalse(self.instance.enabled)

    def test_enable_by_rule_change(self):
        self.instance.set_rule("enabled")
        self.assertTrue(self.instance.enabled)
        self.assertEqual(self.instance.current_rule, "on")

    def test_condition_met(self):
        self.instance.set_rule("on")
        self.assertTrue(self.instance.condition_met())

        self.instance.set_rule("off")
        self.assertFalse(self.instance.condition_met())

        self.instance.set_rule("Disabled")
        self.assertEqual(self.instance.condition_met(), None)

    def test_trigger(self):
        # Ensure current rule is off to avoid false positive
        self.instance.set_rule("off")
        self.assertFalse(self.instance.condition_met())
        # Trigger, condition should now be met
        self.assertTrue(self.instance.trigger())
        self.assertTrue(self.instance.condition_met())

    # Original bug: Some sensor types would crash or behave unexpectedly if default_rule was "enabled" or "disabled" in various
    # situations. These classes now raise exception in init method to prevent this.
    # It should no longer be possible to instantiate with invalid default_rule.
    def test_regression_invalid_default_rule(self):
        # assertRaises fails for some reason, this approach seems reliable
        try:
            test = Dummy("sensor1", "sensor1", "dummy", True, None, "disabled", [])
            # Should not make it to this line, test failed
            self.assertFalse(True)
        except AttributeError:
            # Should raise exception, test passed
            self.assertTrue(True)

        try:
            test = Dummy("sensor1", "sensor1", "dummy", True, None, "enabled", [])
            # Should not make it to this line, test failed
            self.assertFalse(True)
        except AttributeError:
            # Should raise exception, test passed
            self.assertTrue(True)
