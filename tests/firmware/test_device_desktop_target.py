import json
import unittest
import requests
from DesktopTarget import DesktopTarget

# Read mock API receiver address
with open('config.json', 'r') as file:
    config = json.load(file)

# Get mock command receiver address
ip = config["mock_receiver"]["ip"]
port = config["mock_receiver"]["port"]


class TestDesktopTarget(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.instance = DesktopTarget("device1", "device1", "desktop", "enabled", {}, ip, port)

    def test_01_initial_state(self):
        self.assertIsInstance(self.instance, DesktopTarget)
        self.assertTrue(self.instance.enabled)

    def test_02_turn_on(self):
        self.assertTrue(self.instance.send(1))

    def test_03_turn_off(self):
        # Call twice, mock receiver alternates between user idle and not idle response
        # Both should return True, only difference is log message
        self.assertTrue(self.instance.send(0))
        self.assertTrue(self.instance.send(0))

    def test_04_turn_on_while_disabled(self):
        self.instance.disable()
        self.assertTrue(self.instance.send(1))
        self.instance.enable()

    def test_05_turn_off_while_user_not_idle(self):
        # Configure mock receiver to simulate user active in last 10ms
        requests.post(f'http://{ip}:{port}/set_idle_time', json={'idle_time': 10})
        # Turn off, confirm method returns True despite not turning off screen
        # (prevents group repeatedly trying to turn off while user active)
        self.assertTrue(self.instance.send(0))

    def test_06_network_errors(self):
        # Change to invalid IP to simulate failed connection, confirm send returns False
        self.instance.uri = f'0.0.0.:{config["mock_receiver"]["port"]}'
        self.assertFalse(self.instance.send(1))

        # Change port to error port, configure mock receiver to return 400 error
        uri = f'{config["mock_receiver"]["ip"]}:{config["mock_receiver"]["error_port"]}'
        requests.get(f'http://{uri}/set_bad_request_error')
        self.instance.uri = uri
        # Confirm send method returns False, confirm instance is disabled
        self.assertFalse(self.instance.send(1))
        self.assertFalse(self.instance.enabled)

        # Confirm send method returns False when turning off while disabled
        self.assertFalse(self.instance.send(0))
