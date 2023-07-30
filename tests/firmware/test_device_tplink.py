import json
import unittest
from Tplink import Tplink

# Read mock API receiver address
with open('config.json', 'r') as file:
    config = json.load(file)


class TestTplink(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.instance = Tplink("device1", "device1", "dimmer", 42, 1, 100, config["mock_receiver"]["ip"])

    def test_01_initial_state(self):
        self.assertIsInstance(self.instance, Tplink)
        self.assertTrue(self.instance.enabled)
        self.assertFalse(self.instance.fading)

    def test_02_turn_off(self):
        self.assertTrue(self.instance.send(0))

        # Repeat as bulb
        self.instance._type = "bulb"
        self.assertTrue(self.instance.send(0))

    def test_03_turn_on(self):
        self.assertTrue(self.instance.send(1))

        # Repeat as dimmer
        self.instance._type = "dimmer"
        self.assertTrue(self.instance.send(1))

    def test_04_turn_on_while_disabled(self):
        self.instance.disable()
        self.assertTrue(self.instance.send(1))
        self.instance.enable()

    def test_05_send_method_error(self):
        # Instantiate with invalid IP, confirm send method returns False
        test = Tplink("device1", "device1", "dimmer", 42, 1, 100, "0.0.0.")
        self.assertFalse(test.send())
