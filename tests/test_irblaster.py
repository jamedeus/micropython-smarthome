import unittest
from IrBlaster import IrBlaster



class TestIrBlaster(unittest.TestCase):

    def __init__(self):
        self.instance = IrBlaster(4, "both")

    def test_instantiation(self):
        self.assertIsInstance(self.instance, IrBlaster)
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
