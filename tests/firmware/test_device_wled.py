import json
import unittest
from Wled import Wled

# Read mock API receiver address
with open('config.json', 'r') as file:
    config = json.load(file)

# IP and port of mock API receiver instance
mock_address = f"{config['mock_receiver']['ip']}:{config['mock_receiver']['port']}"


class TestWled(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.instance = Wled("device1", "device1", "wled", 50, 1, 255, mock_address)

    def test_01_initial_state(self):
        self.assertIsInstance(self.instance, Wled)
        self.assertTrue(self.instance.enabled)

    def test_02_turn_off(self):
        self.assertTrue(self.instance.send(0))

    def test_03_turn_on(self):
        self.assertTrue(self.instance.send(1))

    def test_04_turn_on_while_disabled(self):
        self.instance.disable()
        self.assertTrue(self.instance.send(1))
        self.instance.enable()

    def test_05_network_errors(self):
        # Instantiate with invalid IP, confirm send method returns False
        test = Wled("device1", "device1", "wled", 50, 1, 255, "0.0.0.")
        self.assertFalse(test.send())

        # Set invalid rule to trigger 400 status code, confirm send returns False
        self.instance.current_rule = 9999
        self.assertFalse(self.instance.send())
