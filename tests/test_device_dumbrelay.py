import unittest
from DumbRelay import DumbRelay


class TestDumbRelay(unittest.TestCase):

    def __dir__(self):
        return [
            "test_instantiation",
            "test_rule_validation_valid",
            "test_rule_validation_invalid",
            "test_rule_change",
            "test_enable_disable",
            "test_disable_by_rule_change",
            "test_enable_by_rule_change",
            "test_turn_on",
            "test_turn_off",
            "test_regression_turn_off_while_disabled"
        ]

    def test_instantiation(self):
        self.instance = DumbRelay("device1", "device1", "dumb-relay", True, None, "enabled", 4)
        self.assertIsInstance(self.instance, DumbRelay)
        self.assertFalse(self.instance.relay.value())
        self.assertTrue(self.instance.enabled)

    def test_rule_validation_valid(self):
        self.assertIs(self.instance.rule_validator("Disabled"), "disabled")
        self.assertIs(self.instance.rule_validator("DISABLED"), "disabled")
        self.assertIs(self.instance.rule_validator("Enabled"), "enabled")
        self.assertIs(self.instance.rule_validator("enabled"), "enabled")

    def test_rule_validation_invalid(self):
        self.assertFalse(self.instance.rule_validator(True))
        self.assertFalse(self.instance.rule_validator(None))
        self.assertFalse(self.instance.rule_validator("string"))
        self.assertFalse(self.instance.rule_validator(42))
        self.assertFalse(self.instance.rule_validator("on"))
        self.assertFalse(self.instance.rule_validator("off"))
        self.assertFalse(self.instance.rule_validator(["enabled"]))
        self.assertFalse(self.instance.rule_validator({"disabled": "disabled"}))

    def test_rule_change(self):
        self.assertTrue(self.instance.set_rule("disabled"))
        self.assertEqual(self.instance.current_rule, 'disabled')
        self.assertTrue(self.instance.set_rule("enabled"))
        self.assertEqual(self.instance.current_rule, 'enabled')

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

    def test_turn_on(self):
        self.assertTrue(self.instance.send(1))
        self.assertEqual(self.instance.relay.value(), 1)

    def test_turn_off(self):
        self.assertTrue(self.instance.send(0))
        self.assertEqual(self.instance.relay.value(), 0)

    # Original bug: Disabled devices manually turned on by user could not be turned off by loop.
    # This became an issue when on/off rules were removed, requiring use of enabled/disabled.
    # After fix disabled devices may be turned off, preventing lights from getting stuck. Disabled
    # devices do NOT respond to on commands, but do flip their state to True to stay in sync with
    # rest of group - this is necessary to allow turning off, since a device with state == False
    # will be skipped by loop (already off), and user flipping light switch doesn't effect state
    def test_regression_turn_off_while_disabled(self):
        # Disable, confirm disabled and off
        self.instance.disable()
        self.assertFalse(self.instance.enabled)
        self.assertEqual(self.instance.relay.value(), 0)

        # Manually turn on while disabled
        self.instance.relay.value(1)

        # Off command should still return True, should revert override
        self.assertTrue(self.instance.send(0))
        self.assertEqual(self.instance.relay.value(), 0)

        # On command should also return True, but shouldn't cause any action
        self.assertTrue(self.instance.send(1))
        self.assertEqual(self.instance.relay.value(), 0)
