import unittest
from machine import Pin
from DumbRelay import DumbRelay


class TestDumbRelay(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.instance = DumbRelay("device1", "device1", "dumb-relay", "enabled", 4)

    def test_01_initial_state(self):
        self.assertIsInstance(self.instance, DumbRelay)
        self.assertFalse(self.instance.relay.value())
        self.assertTrue(self.instance.enabled)

    def test_02_turn_on(self):
        self.assertTrue(self.instance.send(1))
        self.assertEqual(self.instance.relay.value(), 1)

    def test_03_turn_off(self):
        self.assertTrue(self.instance.send(0))
        self.assertEqual(self.instance.relay.value(), 0)

    # Original bug: Disabled devices manually turned on by user could not be turned off by loop.
    # This became an issue when on/off rules were removed, requiring use of enabled/disabled.
    # After fix disabled devices may be turned off, preventing lights from getting stuck. Disabled
    # devices do NOT respond to on commands, but do flip their state to True to stay in sync with
    # rest of group - this is necessary to allow turning off, since a device with state == False
    # will be skipped by loop (already off), and user flipping light switch doesn't effect state
    def test_04_regression_turn_off_while_disabled(self):
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

    # Original bug: Config.__init__ formerly contained a conditional to instantiate devices
    # in the appropriate class, which cast pin arguments to int. When this was replaced with a
    # factory pattern in c9a8eae9 the type casting was lost, leading to a crash when config
    # file contained a string pin. Fixed by casting to int in device init methods.
    def test_05_regression_string_pin_number(self):
        # Attempt to instantiate with a string pin number
        self.instance = DumbRelay("device1", "device1", "dumb-relay", "enabled", "4")
        self.assertIsInstance(self.instance, DumbRelay)
        self.assertIsInstance(self.instance.relay, Pin)
