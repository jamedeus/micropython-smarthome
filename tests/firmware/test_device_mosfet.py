import unittest
from machine import Pin
from Mosfet import Mosfet


class TestMosfet(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.instance = Mosfet("device1", "device1", "mosfet", "enabled", 4)

    def test_01_initial_state(self):
        self.assertIsInstance(self.instance, Mosfet)
        self.assertFalse(self.instance.mosfet.value())
        self.assertTrue(self.instance.enabled)

    def test_02_turn_on(self):
        self.assertTrue(self.instance.send(1))
        self.assertEqual(self.instance.mosfet.value(), 1)

    def test_03_turn_off(self):
        self.assertTrue(self.instance.send(0))
        self.assertEqual(self.instance.mosfet.value(), 0)

    def test_04_enable_after_disable_by_rule_change(self):
        # Disable by rule change, enable with method
        self.instance.set_rule("disabled")
        self.instance.enable()
        # Old rule ("disabled") should have been automatically replaced by scheduled_rule
        self.assertEqual(self.instance.current_rule, self.instance.scheduled_rule)

    # Original bug: Disabled devices manually turned on by user could not be turned off by loop.
    # This became an issue when on/off rules were removed, requiring use of enabled/disabled.
    # After fix disabled devices may be turned off, preventing lights from getting stuck. Disabled
    # devices do NOT respond to on commands, but do flip their state to True to stay in sync with
    # rest of group - this is necessary to allow turning off, since a device with state == False
    # will be skipped by loop (already off), and user flipping light switch doesn't effect state
    def test_05_regression_turn_off_while_disabled(self):
        # Disable, confirm disabled and off
        self.instance.disable()
        self.assertFalse(self.instance.enabled)
        self.assertEqual(self.instance.mosfet.value(), 0)

        # Manually turn on while disabled
        self.instance.mosfet.value(1)

        # Off command should still return True, should revert override
        self.assertTrue(self.instance.send(0))
        self.assertEqual(self.instance.mosfet.value(), 0)

        # On command should also return True, but shouldn't cause any action
        self.assertTrue(self.instance.send(1))
        self.assertEqual(self.instance.mosfet.value(), 0)

    # Original bug: Config.__init__ formerly contained a conditional to instantiate devices
    # in the appropriate class, which cast pin arguments to int. When this was replaced with a
    # factory pattern in c9a8eae9 the type casting was lost, leading to a crash when config
    # file contained a string pin. Fixed by casting to int in device init methods.
    def test_06_regression_string_pin_number(self):
        # Attempt to instantiate with a string pin number
        self.instance = Mosfet("device1", "device1", "mosfet", "enabled", "4")
        self.assertIsInstance(self.instance, Mosfet)
        self.assertIsInstance(self.instance.mosfet, Pin)
