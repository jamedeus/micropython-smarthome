import unittest
from Relay import Relay



class TestRelay(unittest.TestCase):

    def __dir__(self):
        return ["test_instantiation", "test_rule_validation_valid", "test_rule_validation_invalid", "test_rule_change", "test_enable_disable", "test_disable_by_rule_change", "test_enable_by_rule_change", "test_turn_on", "test_turn_off", "test_turn_on_while_rule_is_off"]

    def test_instantiation(self):
        self.instance = Relay("device1", "relay", True, "on", "on", "192.168.1.202")
        self.assertIsInstance(self.instance, Relay)
        self.assertTrue(self.instance.enabled)

    def test_rule_validation_valid(self):
        self.assertIs(self.instance.rule_validator("on"), "on")
        self.assertIs(self.instance.rule_validator("On"), "on")
        self.assertIs(self.instance.rule_validator("ON"), "on")
        self.assertIs(self.instance.rule_validator("off"), "off")
        self.assertIs(self.instance.rule_validator("Disabled"), "disabled")

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
        self.instance.set_rule("on")
        self.assertTrue(self.instance.enabled)

    def test_turn_on(self):
        self.assertTrue(self.instance.send(1))
        self.assertEqual(self.instance.check_state(), 'ON')

    def test_turn_off(self):
        self.assertTrue(self.instance.send(0))
        self.assertEqual(self.instance.check_state(), 'OFF')

    def test_turn_on_while_rule_is_off(self):
        self.instance.set_rule("off")
        # Make sure current state is OFF before attempting to turn on
        self.assertTrue(self.instance.send(0))
        # Attempt to turn on
        self.assertTrue(self.instance.send(1))
        # Should have ignored send command since current_rule == "off"
        self.assertEqual(self.instance.check_state(), 'OFF')
