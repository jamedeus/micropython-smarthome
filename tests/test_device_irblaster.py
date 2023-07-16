import unittest
from ir_tx import Player
from IrBlaster import IrBlaster


class TestIrBlaster(unittest.TestCase):

    def __dir__(self):
        return [
            "test_initial_state",
            "test_send_valid",
            "test_send_invalid"
        ]

    @classmethod
    def setUpClass(cls):
        cls.instance = IrBlaster("4", ["tv", "ac"])

    def test_initial_state(self):
        self.assertIsInstance(self.instance, IrBlaster)
        self.assertIsInstance(self.instance.ir, Player)
        self.assertEqual(len(self.instance.codes), 2)
        self.assertEqual(len(self.instance.codes['ac']), 10)
        self.assertEqual(len(self.instance.codes['tv']), 12)

    def test_send_valid(self):
        # Test keys that exist
        self.assertTrue(self.instance.send("tv", "power"))
        self.assertTrue(self.instance.send("tv", "vol_down"))
        self.assertTrue(self.instance.send("tv", "vol_up"))
        self.assertTrue(self.instance.send("ac", "OFF"))
        self.assertTrue(self.instance.send("ac", "ON"))

    def test_send_invalid(self):
        # Test keys that don't exist
        self.assertFalse(self.instance.send("tv", "on"))
        self.assertFalse(self.instance.send("tv", "vol_mute"))
        self.assertFalse(self.instance.send("ac", "cool"))
        self.assertFalse(self.instance.send("ac", "hot"))
        self.assertFalse(self.instance.send("ac", 2))
        self.assertFalse(self.instance.send(5, "foo"))
