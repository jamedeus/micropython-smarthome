import unittest
from LedStrip import LedStrip



class TestLedStrip(unittest.TestCase):

    def __dir__(self):
        return ["test_instantiation", "test_rule_validation_valid", "test_rule_validation_invalid", "test_rule_change", "test_enable_disable", "test_disable_by_rule_change", "test_enable_by_rule_change", "test_turn_on", "test_turn_off"]

    def test_instantiation(self):
        self.instance = LedStrip("device1", "pwm", True, None, "off", 4, 0, 1023)
        self.assertIsInstance(self.instance, LedStrip)
        self.assertFalse(self.instance.pwm.duty())
        self.assertTrue(self.instance.enabled)

    def test_rule_validation_valid(self):
        self.assertEqual(self.instance.rule_validator(1), 1)
        self.assertEqual(self.instance.rule_validator(512), 512)
        self.assertEqual(self.instance.rule_validator(1023), 1023)
        self.assertEqual(self.instance.rule_validator("1023"), 1023)
        self.assertEqual(self.instance.rule_validator("Disabled"), "disabled")
        self.assertEqual(self.instance.rule_validator("fade/345/120"), "fade/345/120")
        self.assertEqual(self.instance.rule_validator("fade/1021/120000"), "fade/1021/120000")

    def test_rule_validation_invalid(self):
        self.assertFalse(self.instance.rule_validator(True))
        self.assertFalse(self.instance.rule_validator(None))
        self.assertFalse(self.instance.rule_validator("string"))
        self.assertFalse(self.instance.rule_validator(-42))
        self.assertFalse(self.instance.rule_validator("-42"))
        self.assertFalse(self.instance.rule_validator(1337))
        self.assertFalse(self.instance.rule_validator([500]))
        self.assertFalse(self.instance.rule_validator({500:500}))
        self.assertFalse(self.instance.rule_validator(["fade", "500", "1200"]))
        self.assertFalse(self.instance.rule_validator("fade/2000/15"))
        self.assertFalse(self.instance.rule_validator("fade/-512/600"))
        self.assertFalse(self.instance.rule_validator("fade/512/-600"))
        self.assertFalse(self.instance.rule_validator("fade/None/None"))
        self.assertFalse(self.instance.rule_validator("fade/1023/None"))
        self.assertFalse(self.instance.rule_validator("fade/None/120"))

    def test_rule_change(self):
        self.assertTrue(self.instance.set_rule(1023))
        self.assertEqual(self.instance.current_rule, 1023)

    def test_enable_disable(self):
        self.instance.disable()
        self.assertFalse(self.instance.enabled)
        self.instance.enable()
        self.assertTrue(self.instance.enabled)

    def test_disable_by_rule_change(self):
        self.instance.set_rule("Disabled")
        self.assertFalse(self.instance.enabled)

    def test_enable_by_rule_change(self):
        self.instance.set_rule(512)
        self.assertTrue(self.instance.enabled)

    def test_turn_on(self):
        self.instance.set_rule(32)
        self.assertTrue(self.instance.send(1))
        self.assertEqual(self.instance.pwm.duty(), 32)

    def test_turn_off(self):
        self.instance.enable()
        self.assertTrue(self.instance.send(0))
        self.assertEqual(self.instance.pwm.duty(), 0)
