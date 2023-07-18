import unittest
from machine import PWM
from LedStrip import LedStrip

# Expected return value of get_attributes method just after instantiation
expected_attributes = {
    'min_bright': 0,
    'nickname': 'device1',
    'max_bright': 1023,
    '_type': 'pwm',
    'scheduled_rule': None,
    'current_rule': None,
    'default_rule': 512,
    'enabled': True,
    'rule_queue': [],
    'state': None,
    'name': 'device1',
    'triggered_by': [],
    'bright': 0,
    'fading': False
}


class TestLedStrip(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.instance = LedStrip("device1", "device1", "pwm", 512, 0, 1023, 4)

    def test_01_initial_state(self):
        self.assertIsInstance(self.instance, LedStrip)
        self.assertFalse(self.instance.pwm.duty())
        self.assertTrue(self.instance.enabled)

    def test_02_get_attributes(self):
        attributes = self.instance.get_attributes()
        self.assertEqual(attributes, expected_attributes)

    def test_03_rule_validation_valid(self):
        self.assertEqual(self.instance.rule_validator(1), 1)
        self.assertEqual(self.instance.rule_validator(512), 512)
        self.assertEqual(self.instance.rule_validator(1023), 1023)
        self.assertEqual(self.instance.rule_validator("1023"), 1023)
        self.assertEqual(self.instance.rule_validator("Disabled"), "disabled")
        self.assertEqual(self.instance.rule_validator("Enabled"), "enabled")
        self.assertEqual(self.instance.rule_validator("fade/345/120"), "fade/345/120")
        self.assertEqual(self.instance.rule_validator("fade/1021/120000"), "fade/1021/120000")

    def test_04_rule_validation_invalid(self):
        self.assertFalse(self.instance.rule_validator(True))
        self.assertFalse(self.instance.rule_validator(None))
        self.assertFalse(self.instance.rule_validator("string"))
        self.assertFalse(self.instance.rule_validator(-42))
        self.assertFalse(self.instance.rule_validator("-42"))
        self.assertFalse(self.instance.rule_validator(1337))
        self.assertFalse(self.instance.rule_validator([500]))
        self.assertFalse(self.instance.rule_validator({500: 500}))
        self.assertFalse(self.instance.rule_validator(["fade", "500", "1200"]))
        self.assertFalse(self.instance.rule_validator("fade/2000/15"))
        self.assertFalse(self.instance.rule_validator("fade/-512/600"))
        self.assertFalse(self.instance.rule_validator("fade/512/-600"))
        self.assertFalse(self.instance.rule_validator("fade/None/None"))
        self.assertFalse(self.instance.rule_validator("fade/1023/None"))
        self.assertFalse(self.instance.rule_validator("fade/None/120"))

    def test_05_rule_change(self):
        self.assertTrue(self.instance.set_rule(1023))
        self.assertEqual(self.instance.current_rule, 1023)

    def test_06_enable_disable(self):
        self.instance.disable()
        self.assertFalse(self.instance.enabled)
        self.instance.enable()
        self.assertTrue(self.instance.enabled)

    def test_07_disable_by_rule_change(self):
        self.instance.set_rule("Disabled")
        self.assertFalse(self.instance.enabled)

    def test_08_enable_by_rule_change(self):
        self.instance.set_rule(512)
        self.assertTrue(self.instance.enabled)

    def test_09_turn_on(self):
        self.instance.set_rule(32)
        self.assertTrue(self.instance.send(1))
        self.assertEqual(self.instance.pwm.duty(), 32)

    def test_10_turn_off(self):
        self.instance.enable()
        self.assertTrue(self.instance.send(0))
        self.assertEqual(self.instance.pwm.duty(), 0)

    # TODO not sure why this fails, seems like self.bright is NoneType?
    # IDK how this would happen, very strange
    def test_11_turn_off_when_disabled(self):
        # Ensure turned on and enabled
        self.instance.enable()
        self.instance.send(1)
        self.assertEqual(self.instance.pwm.duty(), self.instance.current_rule)
        # Manually set state (normally done by main loop)
        self.instance.state = True

        # Disable - should automatically turn off, state should flip
        self.instance.disable()
        self.assertEqual(self.instance.pwm.duty(), 0)
        self.assertFalse(self.instance.state)

    # Original bug: Enabling and turning on when both current and scheduled rules == "disabled"
    # resulted in comparison operator between int and string, causing crash.
    # After fix (see efd79c6f) this is handled by overwriting current_rule with default_rule.
    def test_12_enable_regression_test(self):
        # Simulate disabling by scheduled rule change
        self.instance.scheduled_rule = "disabled"
        self.instance.set_rule("disabled")
        # Simulate user enabling and turning on from frontend
        self.instance.enable()
        self.instance.send(1)
        # Should not crash, should replace unusable rule with default_rule (512) and fade on
        self.assertNotEqual(self.instance.current_rule, "disabled")
        self.assertEqual(self.instance.current_rule, 512)
        self.assertEqual(self.instance.pwm.duty(), 512)

    # Original bug: LedStrip class overwrites parent set_rule method and did not include conditional
    # that overwrites "enabled" with default_rule. This resulted in an unusable rule which caused
    # crash next time send method was called.
    def test_13_regression_rule_change_to_enabled(self):
        self.instance.disable()
        self.assertFalse(self.instance.enabled)
        self.instance.set_rule('enabled')
        # Rule should be set to default rule, NOT 'enabled'
        self.assertEqual(self.instance.current_rule, 512)
        self.assertTrue(self.instance.enabled)
        # Attempt to reproduce crash, should not crash
        self.assertTrue(self.instance.send(1))

    # Original bug: Devices that use current_rule in send() payload crashed if default_rule was "enabled" or "disabled"
    # and current_rule changed to "enabled" (string rule instead of int in payload). These classes now raise exception
    # in init method to prevent this. It should no longer be possible to instantiate with invalid default_rule.
    def test_14_regression_invalid_default_rule(self):
        # assertRaises fails for some reason, this approach seems reliable
        try:
            LedStrip("device1", "device1", "pwm", "disabled", 0, 1023, 4)
            # Should not make it to this line, test failed
            self.assertFalse(True)
        except AttributeError:
            # Should raise exception, test passed
            self.assertTrue(True)

        try:
            LedStrip("device1", "device1", "pwm", "enabled", 0, 1023, 4)
            # Should not make it to this line, test failed
            self.assertFalse(True)
        except AttributeError:
            # Should raise exception, test passed
            self.assertTrue(True)

    # Original bug: Disabled devices manually turned on by user could not be turned off by loop.
    # This became an issue when on/off rules were removed, requiring use of enabled/disabled.
    # After fix disabled devices may be turned off, preventing lights from getting stuck. Disabled
    # devices do NOT respond to on commands, but do flip their state to True to stay in sync with
    # rest of group - this is necessary to allow turning off, since a device with state == False
    # will be skipped by loop (already off), and user flipping light switch doesn't effect state
    def test_15_regression_turn_off_while_disabled(self):
        # Disable, confirm disabled and off
        self.instance.send(0)
        self.instance.disable()
        self.assertFalse(self.instance.enabled)
        self.assertEqual(self.instance.pwm.duty(), 0)

        # Manually turn on while disabled
        self.instance.pwm.duty(512)
        self.instance.bright = 512

        # Off command should still return True, should revert override
        self.assertTrue(self.instance.send(0))
        self.assertEqual(self.instance.pwm.duty(), 0)

        # On command should also return True, but shouldn't cause any action
        self.assertTrue(self.instance.send(1))
        self.assertEqual(self.instance.pwm.duty(), 0)

    def test_16_regression_rule_change_while_fading(self):
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

    # Original bug: Config.__init__ formerly contained a conditional to instantiate devices
    # in the appropriate class, which cast pin arguments to int. When this was replaced with a
    # factory pattern in c9a8eae9 the type casting was lost, leading to a crash when config
    # file contained a string pin. Fixed by casting to int in device init methods.
    def test_17_regression_string_pin_number(self):
        # Attempt to instantiate with a string pin number
        self.instance = LedStrip("device1", "device1", "pwm", 512, 0, 1023, "4")
        self.assertIsInstance(self.instance, LedStrip)
        self.assertIsInstance(self.instance.pwm, PWM)

    # Original issue: DimmableLight.set_rule contains a conditional to abort an in-progress fade if
    # brightness is changed in the opposite direction. This is determined by checking if the new rule
    # is greater/less than current_rule, with no type checking on the new rule. This resulted in a
    # traceback when rule changed to a string (enabled, disabled) while fading.
    # Should now skip conditional if new rule is non-integer.
    def test_18_regression_rule_change_to_disabled_while_fading(self):
        # Set starting brightness
        self.instance.set_rule(50)
        self.assertEqual(self.instance.current_rule, 50)

        # Start fading DOWN, confirm started
        self.instance.set_rule('fade/30/1800')
        self.assertTrue(self.instance.fading)

        # Change rule to disabled, confirm changed, confirm no longer fading
        self.instance.set_rule('disabled')
        self.assertEqual(self.instance.current_rule, 'disabled')
        self.assertFalse(self.instance.fading)
