import unittest
from machine import PWM
from LedStrip import LedStrip

# Expected return value of get_attributes method just after instantiation
expected_attributes = {
    'min_rule': 0,
    'nickname': 'device1',
    'max_rule': 1023,
    '_type': 'pwm',
    'scheduled_rule': None,
    'current_rule': None,
    'default_rule': 512,
    'enabled': True,
    "group": None,
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

    def test_03_turn_on(self):
        self.instance.set_rule(32)
        self.assertTrue(self.instance.send(1))
        self.assertEqual(self.instance.pwm.duty(), 32)

    def test_04_turn_off(self):
        self.instance.enable()
        self.assertTrue(self.instance.send(0))
        self.assertEqual(self.instance.pwm.duty(), 0)

    def test_05_turn_off_when_disabled(self):
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
    def test_06_enable_regression_test(self):
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

    # Original bug: Disabled devices manually turned on by user could not be turned off by loop.
    # This became an issue when on/off rules were removed, requiring use of enabled/disabled.
    # After fix disabled devices may be turned off, preventing lights from getting stuck. Disabled
    # devices do NOT respond to on commands, but do flip their state to True to stay in sync with
    # rest of group - this is necessary to allow turning off, since a device with state == False
    # will be skipped by loop (already off), and user flipping light switch doesn't effect state
    def test_07_regression_turn_off_while_disabled(self):
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

    # Original bug: Config.__init__ formerly contained a conditional to instantiate devices
    # in the appropriate class, which cast pin arguments to int. When this was replaced with a
    # factory pattern in c9a8eae9 the type casting was lost, leading to a crash when config
    # file contained a string pin. Fixed by casting to int in device init methods.
    def test_08_regression_string_pin_number(self):
        # Attempt to instantiate with a string pin number
        self.instance = LedStrip("device1", "device1", "pwm", 512, 0, 1023, "4")
        self.assertIsInstance(self.instance, LedStrip)
        self.assertIsInstance(self.instance.pwm, PWM)

    # Original bug: Enable method handled current_rule == 'disabled' by arbitrarily setting
    # scheduled_rule as current_rule with no validation. This made it possible for a string
    # representation of int to be set as current_rule, raising exception when send method
    # called. Now uses set_rule method to cast rule to required type.
    def test_09_regression_string_int_rule(self):
        # Set scheduled_rule to string representation of int
        self.instance.scheduled_rule = '512'

        # Set rule to disabled to trigger first conditional in enable method
        self.instance.set_rule('disabled')
        self.assertEqual(self.instance.current_rule, 'disabled')

        # Enable, should fall back to scheduled_rule and cast to int
        self.instance.enable()
        self.assertEqual(self.instance.current_rule, 512)

        # Call send method, should not crash
        self.instance.send(1)
