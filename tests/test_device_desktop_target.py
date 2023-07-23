import json
import unittest
import SoftwareTimer
from Desktop_target import Desktop_target

# Read mock API receiver address
with open('config.json', 'r') as file:
    config = json.load(file)


class TestDesktopTarget(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        ip = config["mock_receiver"]["ip"]
        port = config["mock_receiver"]["port"]
        cls.instance = Desktop_target("device1", "device1", "desktop", "enabled", ip, port)

    def test_01_initial_state(self):
        self.assertIsInstance(self.instance, Desktop_target)
        self.assertTrue(self.instance.enabled)

    def test_02_turn_off(self):
        # Confirm instance does not have timer in queue
        SoftwareTimer.timer.cancel(self.instance.name)
        self.assertTrue(self.instance.name not in str(SoftwareTimer.timer.schedule))
        # Turn off, confirm timer added to queue
        self.assertTrue(self.instance.send(0))
        self.assertIn(self.instance.name, str(SoftwareTimer.timer.schedule))
        SoftwareTimer.timer.cancel(self.instance.name)

    def test_03_turn_on(self):
        self.assertTrue(self.instance.send(1))

    def test_04_turn_on_while_disabled(self):
        self.instance.disable()
        self.assertTrue(self.instance.send(1))
        self.instance.enable()

    def test_05_off_method(self):
        # Call method twice for full coverage
        # Mock receiver alternates between short and long idle time values
        self.instance.off()
        self.instance.off()

        # Call with invalid IP to trigger network error, confirm timer added to queue
        SoftwareTimer.timer.cancel(self.instance.name)
        self.assertTrue(self.instance.name not in str(SoftwareTimer.timer.schedule))
        self.instance.ip = "0.0.0."
        self.instance.off()
        self.assertIn(self.instance.name, str(SoftwareTimer.timer.schedule))
        SoftwareTimer.timer.cancel(self.instance.name)
        self.instance.ip = config["mock_receiver"]["ip"]

        # Simulate error due to non-JSON response, instance should be disabled
        self.instance.port = config["mock_receiver"]["error_port"]
        self.instance.off()
        self.assertFalse(self.instance.enabled)
        self.instance.enable()

    def test_06_network_errors(self):
        # Change to invalid IP to simulate failed connection, confirm send returns False
        self.instance.ip = "0.0.0."
        self.assertFalse(self.instance.send(1))
        self.instance.ip = config["mock_receiver"]["ip"]

        # Change port to error port (mock receiver returns error for all requests on this port)
        # Confirm send method returns False
        self.instance.port = config["mock_receiver"]["error_port"]
        self.instance.send(1)
        self.assertFalse(self.instance.enabled)
        self.instance.port = config["mock_receiver"]["port"]
