import json
import unittest
from TasmotaRelay import TasmotaRelay

# Read mock API receiver address
with open('config.json', 'r') as file:
    config = json.load(file)

# IP and port of mock API receiver instance
mock_address = f"{config['mock_receiver']['ip']}:{config['mock_receiver']['port']}"


class TestTasmotaRelay(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.instance = TasmotaRelay("device1", "device1", "tasmota-relay", "enabled", {}, mock_address)

    def test_01_initial_state(self):
        self.assertIsInstance(self.instance, TasmotaRelay)
        self.assertTrue(self.instance.enabled)
        self.assertEqual(self.instance.uri, mock_address)

    def test_02_turn_on(self):
        self.assertTrue(self.instance.send(1))
        self.assertEqual(self.instance.check_state(), 'ON')

    def test_03_turn_off(self):
        self.assertTrue(self.instance.send(0))
        self.assertEqual(self.instance.check_state(), 'OFF')

    def test_04_turn_on_while_disabled(self):
        self.instance.disable()
        self.assertTrue(self.instance.send(1))
        self.instance.enable()

    def test_06_get_url(self):
        # Confirm both URLs are correct
        self.assertEqual(self.instance.get_url(0), f'http://{mock_address}/cm?cmnd=Power%20Off')
        self.assertEqual(self.instance.get_url(1), f'http://{mock_address}/cm?cmnd=Power%20On')

    def test_06_network_errors(self):
        # Change port to error port (mock receiver returns error for all requests on this port)
        # Confirm send method returns False
        self.instance.uri = f"{config['mock_receiver']['ip']}:{config['mock_receiver']['error_port']}"
        self.assertFalse(self.instance.send(1))

        # Change to invalid IP, confirm send method returns False
        self.instance.uri = "0.0.0."
        self.assertFalse(self.instance.send(0))
        self.assertFalse(self.instance.send(1))
        self.assertEqual(self.instance.check_state(), "Network Error")

        # Revert URI
        self.instance.uri = mock_address
