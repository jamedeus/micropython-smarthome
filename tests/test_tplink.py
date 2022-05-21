import unittest
from Tplink import Tplink



class TestTplink(unittest.TestCase):

    def test_instantiation(self):
        self.instance = Tplink("device1", "dimmer", True, None, None, "192.168.1.233")
        self.assertIsInstance(self.instance, Tplink)

    def test_initial_state(self):
        self.assertTrue(self.instance.enabled)
        self.assertFalse(self.instance.fading)

    def test_rule_validation_valid(self):
        self.assertEqual(self.instance.rule_validator(1), 1)
        self.assertEqual(self.instance.rule_validator(51), 51)
        self.assertEqual(self.instance.rule_validator("42"), 42)
        self.assertEqual(self.instance.rule_validator("Disabled"), "Disabled")
        self.assertEqual(self.instance.rule_validator("fade/98/120"), "fade/98/120")
        self.assertEqual(self.instance.rule_validator("fade/0/120000"), "fade/0/120000")

    def test_rule_validation_invalid(self):
        self.assertFalse(self.instance.rule_validator(True))
        self.assertFalse(self.instance.rule_validator(None))
        self.assertFalse(self.instance.rule_validator("string"))
        self.assertFalse(self.instance.rule_validator(-42))
        self.assertFalse(self.instance.rule_validator("-42"))
        self.assertFalse(self.instance.rule_validator(1337))
        self.assertFalse(self.instance.rule_validator([51]))
        self.assertFalse(self.instance.rule_validator({51:51}))
        self.assertFalse(self.instance.rule_validator(["fade", "50", "1200"]))
        self.assertFalse(self.instance.rule_validator("fade/2000/15"))
        self.assertFalse(self.instance.rule_validator("fade/-512/600"))
        self.assertFalse(self.instance.rule_validator("fade/512/-600"))
        self.assertFalse(self.instance.rule_validator("fade/None/None"))
        self.assertFalse(self.instance.rule_validator("fade/1023/None"))
        self.assertFalse(self.instance.rule_validator("fade/None/120"))

    def test_rule_change(self):
        self.assertTrue(self.instance.set_rule(50))
        self.assertEqual(self.instance.current_rule, 50)

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
        self.instance.set_rule(98)
        self.assertTrue(self.instance.enabled)

    def test_turn_off(self):
        self.assertTrue(self.instance.send(0))

    def test_turn_on(self):
        self.assertTrue(self.instance.send(1))
