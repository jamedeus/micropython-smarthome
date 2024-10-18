import json
import unittest
from Tplink import Tplink
from cpython_only import cpython_only

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

    def test_06_parse_response(self):
        # Should return True if response does not contain error
        self.assertTrue(self.instance._parse_response(
            '{"smartlife.iot.dimmer":{"set_brightness":{"err_code":0}}}'
        ))
        self.assertTrue(self.instance._parse_response(
            '{"smartlife.iot.smartbulb.lightingservice":{"transition_light_state":{"err_code":0}}}'
        ))

        # Should return False if response contains error
        self.assertFalse(self.instance._parse_response(
            '{"smartlife.iot.dimmer":{"set_brightness":{"err_code":-3,"err_msg":"invalid argument"}}}'
        ))

        # Should return False if response is empty
        self.assertFalse(self.instance._parse_response('{}'))

    @cpython_only
    def test_07_send_detects_errors(self):
        from unittest.mock import patch

        # Simulate error response from dimmer, confirm send returns False
        with patch.object(self.instance, '_send_payload', return_value=False):
            self.assertFalse(self.instance.send(1))

        # Simulate error response on second dimmer request, confirm send returns False
        with patch.object(self.instance, '_send_payload', side_effect=[True, False]):
            self.assertFalse(self.instance.send(1))

        # Simulate error response from bulb, confirm send returns False
        self.instance._type = 'bulb'
        with patch.object(self.instance, '_send_payload', return_value=False):
            self.assertFalse(self.instance.send(1))
