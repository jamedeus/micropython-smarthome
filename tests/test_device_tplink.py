import unittest
from Tplink import Tplink


class TestTplink(unittest.TestCase):

    def __dir__(self):
        return [
            "test_instantiation",
            "test_rule_validation_valid",
            "test_rule_validation_invalid",
            "test_rule_change",
            "test_enable_disable",
            "test_disable_by_rule_change",
            "test_enable_by_rule_change",
            "test_turn_off",
            "test_turn_on",
            "test_regression_rule_change_to_enabled",
            "test_regression_invalid_default_rule",
            "test_rule_change_while_fading",
            "test_regression_rule_change_while_fading"
        ]

    def test_instantiation(self):
        self.instance = Tplink("device1", "device1", "dimmer", 42, "192.168.1.233")
        self.assertIsInstance(self.instance, Tplink)
        self.assertTrue(self.instance.enabled)
        self.assertFalse(self.instance.fading)

    def test_rule_validation_valid(self):
        self.assertEqual(self.instance.rule_validator(1), 1)
        self.assertEqual(self.instance.rule_validator(51), 51)
        self.assertEqual(self.instance.rule_validator("42"), 42)
        self.assertEqual(self.instance.rule_validator("Disabled"), "disabled")
        self.assertEqual(self.instance.rule_validator("enabled"), "enabled")
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
        self.assertFalse(self.instance.rule_validator({51: 51}))
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

    def test_enable_disable(self):
        self.instance.disable()
        self.assertFalse(self.instance.enabled)
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

    def test_rule_change_while_fading(self):
        # Set starting brightness
        self.instance.set_rule(50)
        self.assertEqual(self.instance.current_rule, 50)

        # Start fading DOWN, confirm started
        self.instance.set_rule('fade/30/1800')
        self.assertTrue(self.instance.fading)

        # Set brightness between starting and target, should continue fade
        self.instance.set_rule(40)
        self.assertTrue(self.instance.fading)

        # Set brightness below target, should abort fade
        self.instance.set_rule(25)
        self.assertFalse(self.instance.fading)

        # Start fading UP, confirm started
        self.instance.set_rule('fade/75/1800')
        self.assertTrue(self.instance.fading)

        # Set brightness between starting and target, should continue fade
        self.instance.set_rule(50)
        self.assertTrue(self.instance.fading)

        # Set brightness above target, should abort fade
        self.instance.set_rule(98)
        self.assertFalse(self.instance.fading)

    # Original bug: Tplink class overwrites parent set_rule method and did not include conditional
    # that overwrites "enabled" with default_rule. This resulted in an unusable rule which caused
    # crash next time send method was called.
    def test_regression_rule_change_to_enabled(self):
        self.instance.disable()
        self.assertFalse(self.instance.enabled)
        self.instance.set_rule('enabled')
        # Rule should be set to default rule, NOT 'enabled'
        self.assertEqual(self.instance.current_rule, 42)
        self.assertTrue(self.instance.enabled)
        # Attempt to reproduce crash, should not crash
        self.assertTrue(self.instance.send(1))

    # Original bug: Devices that use current_rule in send() payload crashed if default_rule was "enabled" or "disabled"
    # and current_rule changed to "enabled" (string rule instead of int in payload). These classes now raise exception
    # in init method to prevent this. It should no longer be possible to instantiate with invalid default_rule.
    def test_regression_invalid_default_rule(self):
        # assertRaises fails for some reason, this approach seems reliable
        try:
            Tplink("device1", "device1", "dimmer", "disabled", "192.168.1.233")
            # Should not make it to this line, test failed
            self.assertFalse(True)
        except AttributeError:
            # Should raise exception, test passed
            self.assertTrue(True)

        try:
            Tplink("device1", "device1", "dimmer", "enabled", "192.168.1.233")
            # Should not make it to this line, test failed
            self.assertFalse(True)
        except AttributeError:
            # Should raise exception, test passed
            self.assertTrue(True)

    # Original issue: Possible to change brightness while fading since 3dc1854a. If new rule between
    # start and target, fade does not change brightness until caught up to rule change (prevent undoing
    # user's change). However, if brightness changed in opposite direction, fade would continue and user
    # change undone on next fade step.
    # Should now abort any time rule changed in opposite direction, even if still between start and target
    def test_regression_rule_change_while_fading(self):
        # Set starting brightness
        self.instance.set_rule(50)
        self.assertEqual(self.instance.current_rule, 50)

        # Start fading DOWN, confirm started, skip a few steps, confirm still fading
        self.instance.set_rule('fade/30/1800')
        self.assertTrue(self.instance.fading)
        self.instance.set_rule(40)
        self.assertEqual(self.instance.current_rule, 40)
        self.assertTrue(self.instance.fading)

        # Increase brightness - fade should abort despite being between start and target
        self.instance.set_rule(45)
        self.assertFalse(self.instance.fading)

        # Start fading UP, confirm started, skip a few steps, confirm still fading
        self.instance.set_rule('fade/90/1800')
        self.assertTrue(self.instance.fading)
        self.instance.set_rule(75)
        self.assertEqual(self.instance.current_rule, 75)
        self.assertTrue(self.instance.fading)

        # Decrease brightness - fade should abort despite being between start and target
        self.instance.set_rule(70)
        self.assertFalse(self.instance.fading)
