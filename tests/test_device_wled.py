import json
import unittest
from Wled import Wled

# Read mock API receiver address
with open('config.json', 'r') as file:
    config = json.load(file)

# IP and port of mock API receiver instance
mock_address = f"{config['mock_receiver']['ip']}:{config['mock_receiver']['port']}"

# Expected return value of get_attributes method just after instantiation
expected_attributes = {
    'min_bright': 1,
    'nickname': 'device1',
    'ip': mock_address,
    'max_bright': 255,
    '_type': 'wled',
    'scheduled_rule': None,
    'current_rule': None,
    'default_rule': 50,
    'enabled': True,
    'rule_queue': [],
    'state': None,
    'name': 'device1',
    'triggered_by': [],
    'fading': False
}


class TestWled(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.instance = Wled("device1", "device1", "wled", 50, 1, 255, mock_address)

    def test_01_initial_state(self):
        self.assertIsInstance(self.instance, Wled)
        self.assertTrue(self.instance.enabled)

    def test_02_get_attributes(self):
        attributes = self.instance.get_attributes()
        self.assertEqual(attributes, expected_attributes)

    def test_03_rule_validation_valid(self):
        self.assertEqual(self.instance.rule_validator(1), 1)
        self.assertEqual(self.instance.rule_validator(51), 51)
        self.assertEqual(self.instance.rule_validator(251), 251)
        self.assertEqual(self.instance.rule_validator("42"), 42)
        self.assertEqual(self.instance.rule_validator("Disabled"), "disabled")
        self.assertEqual(self.instance.rule_validator("enabled"), "enabled")
        self.assertEqual(self.instance.rule_validator("fade/123/120"), "fade/123/120")
        self.assertEqual(self.instance.rule_validator("fade/1/120000"), "fade/1/120000")

    def test_04_rule_validation_invalid(self):
        self.assertFalse(self.instance.rule_validator(True))
        self.assertFalse(self.instance.rule_validator(None))
        self.assertFalse(self.instance.rule_validator("string"))
        self.assertFalse(self.instance.rule_validator(0))
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

    def test_05_rule_change(self):
        self.assertTrue(self.instance.set_rule(50))
        self.assertEqual(self.instance.current_rule, 50)

    def test_06_enable_disable(self):
        self.instance.disable()
        self.assertFalse(self.instance.enabled)
        self.instance.enable()
        self.assertTrue(self.instance.enabled)

    def test_07_disable_by_rule_change(self):
        self.instance.set_rule("Disabled")
        self.assertFalse(self.instance.enabled)

    def test_08_enable_by_rule_change(self):
        self.instance.set_rule(255)
        self.assertTrue(self.instance.enabled)

    def test_09_turn_off(self):
        self.assertTrue(self.instance.send(0))

    def test_10_turn_on(self):
        self.assertTrue(self.instance.send(1))

    # Original bug: Devices that use current_rule in send() payload crashed if default_rule was "enabled" or "disabled"
    # and current_rule changed to "enabled" (string rule instead of int in payload). These classes now raise exception
    # in init method to prevent this. It should no longer be possible to instantiate with invalid default_rule.
    def test_11_11_regression_invalid_default_rule(self):
        # assertRaises fails for some reason, this approach seems reliable
        try:
            Wled("device1", "device1", "wled", "disabled", 1, 255, "192.168.1.211")
            # Should not make it to this line, test failed
            self.assertFalse(True)
        except AttributeError:
            # Should raise exception, test passed
            self.assertTrue(True)

        try:
            Wled("device1", "device1", "wled", "enabled", 1, 255, "192.168.1.211")
            # Should not make it to this line, test failed
            self.assertFalse(True)
        except AttributeError:
            # Should raise exception, test passed
            self.assertTrue(True)

    def test_12_rule_change_while_fading(self):
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

    # Original issue: DimmableLight.set_rule contains a conditional to abort an in-progress fade if
    # brightness is changed in the opposite direction. This is determined by checking if the new rule
    # is greater/less than current_rule, with no type checking on the new rule. This resulted in a
    # traceback when rule changed to a string (enabled, disabled) while fading.
    # Should now skip conditional if new rule is non-integer.
    def test_13_regression_rule_change_to_disabled_while_fading(self):
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
