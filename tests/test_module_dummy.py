import unittest
from Dummy import Dummy



class TestDummySensor(unittest.TestCase):

    def __dir__(self):
        return ["test_instantiation", "test_rule_validation_valid", "test_rule_validation_invalid", "test_rule_change", "test_enable_disable", "test_disable_by_rule_change", "test_enable_by_rule_change", "test_condition_met"]

    def test_instantiation(self):
        self.instance = Dummy("sensor1", "dummy", True, None, None, [])
        self.assertIsInstance(self.instance, Dummy)
        self.assertTrue(self.instance.enabled)

    def test_rule_validation_valid(self):
        self.assertIs(self.instance.rule_validator("on"), "on")
        self.assertIs(self.instance.rule_validator("off"), "off")
        self.assertIs(self.instance.rule_validator("Disabled"), "Disabled")

    def test_rule_validation_invalid(self):
        self.assertFalse(self.instance.rule_validator(True))
        self.assertFalse(self.instance.rule_validator(None))
        self.assertFalse(self.instance.rule_validator("string"))
        self.assertFalse(self.instance.rule_validator(42))
        self.assertFalse(self.instance.rule_validator(["on"]))
        self.assertFalse(self.instance.rule_validator({"on":"on"}))
        self.assertFalse(self.instance.rule_validator("On"))
        self.assertFalse(self.instance.rule_validator("ON"))

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
        self.instance.set_rule("on")
        self.assertTrue(self.instance.enabled)

    def test_condition_met(self):
        self.instance.set_rule("on")
        self.assertTrue(self.instance.condition_met())

        self.instance.set_rule("off")
        self.assertFalse(self.instance.condition_met())

        self.instance.set_rule("Disabled")
        self.assertEqual(self.instance.condition_met(), None)
