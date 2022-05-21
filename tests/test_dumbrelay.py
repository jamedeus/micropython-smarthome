import unittest
from DumbRelay import DumbRelay


class TestDumbRelay(unittest.TestCase):

    def test_instantiation(self):
        self.instance = DumbRelay("device1", "dumb-relay", True, None, "off", 4)

    def test_initial_state(self):
        self.assertFalse(self.instance.relay.value())
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

    def test_disable(self):
        self.instance.disable()
        self.assertFalse(self.instance.enabled)

    def test_enable(self):
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
        self.assertEqual(self.instance.relay.value(), 1)

    def test_turn_off(self):
        self.assertTrue(self.instance.send(0))
        self.assertEqual(self.instance.relay.value(), 0)

    def test_turn_on_while_rule_is_off(self):
        self.instance.set_rule("off")
        self.assertTrue(self.instance.send(1))
        # Should have ignored send command since current_rule == "off"
        self.assertEqual(self.instance.relay.value(), 0)
