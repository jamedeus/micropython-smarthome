import json
import unittest
import SoftwareTimer
from Desktop_target import Desktop_target

# Read mock API receiver address
with open('config.json', 'r') as file:
    config = json.load(file)

# Expected return value of get_attributes method just after instantiation
expected_attributes = {
    'triggered_by': [],
    'nickname': 'device1',
    'ip': config['mock_receiver']['ip'],
    'port': config['mock_receiver']['port'],
    'enabled': True,
    'rule_queue': [],
    'state': None,
    'default_rule': 'enabled',
    'name': 'device1',
    '_type': 'desktop',
    'scheduled_rule': None,
    'current_rule': None
}


class TestDesktopTarget(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        ip = config["mock_receiver"]["ip"]
        port = config["mock_receiver"]["port"]
        cls.instance = Desktop_target("device1", "device1", "desktop", "enabled", ip, port)

    def test_01_initial_state(self):
        self.assertIsInstance(self.instance, Desktop_target)
        self.assertTrue(self.instance.enabled)

    def test_02_get_attributes(self):
        attributes = self.instance.get_attributes()
        self.assertEqual(attributes, expected_attributes)

    def test_03_rule_validation_valid(self):
        self.assertEqual(self.instance.rule_validator("Disabled"), "disabled")
        self.assertEqual(self.instance.rule_validator("DISABLED"), "disabled")
        self.assertEqual(self.instance.rule_validator("Enabled"), "enabled")
        self.assertEqual(self.instance.rule_validator("enabled"), "enabled")

    def test_04_rule_validation_invalid(self):
        self.assertFalse(self.instance.rule_validator(True))
        self.assertFalse(self.instance.rule_validator(None))
        self.assertFalse(self.instance.rule_validator("string"))
        self.assertFalse(self.instance.rule_validator(42))
        self.assertFalse(self.instance.rule_validator("on"))
        self.assertFalse(self.instance.rule_validator("off"))
        self.assertFalse(self.instance.rule_validator(["enabled"]))
        self.assertFalse(self.instance.rule_validator({"disabled": "disabled"}))

    def test_05_rule_change(self):
        self.assertTrue(self.instance.set_rule("disabled"))
        self.assertEqual(self.instance.current_rule, 'disabled')
        self.assertTrue(self.instance.set_rule("enabled"))
        self.assertEqual(self.instance.current_rule, 'enabled')

    def test_06_enable_disable(self):
        self.instance.disable()
        self.assertFalse(self.instance.enabled)
        self.instance.enable()
        self.assertTrue(self.instance.enabled)

    def test_07_disable_by_rule_change(self):
        self.instance.set_rule("Disabled")
        self.assertFalse(self.instance.enabled)

    def test_08_enable_by_rule_change(self):
        self.instance.set_rule("enabled")
        self.assertTrue(self.instance.enabled)

    def test_09_turn_off(self):
        # Confirm instance does not have timer in queue
        SoftwareTimer.timer.cancel(self.instance.name)
        self.assertTrue(self.instance.name not in str(SoftwareTimer.timer.schedule))
        # Turn off, confirm timer added to queue
        self.assertTrue(self.instance.send(0))
        self.assertIn(self.instance.name, str(SoftwareTimer.timer.schedule))
        SoftwareTimer.timer.cancel(self.instance.name)

    def test_10_turn_on(self):
        self.assertTrue(self.instance.send(1))

    def test_11_turn_on_while_disabled(self):
        self.instance.disable()
        self.assertTrue(self.instance.send(1))
        self.instance.enable()

    def test_12_off_method(self):
        # Call method twice for full coverage
        # Mock receiver alternates between short and long idle time values
        self.instance.off()
        self.instance.off()

        # Call with invalid IP to trigger network error, confirm timer added to queue
        SoftwareTimer.timer.cancel(self.instance.name)
        self.assertTrue(self.instance.name not in str(SoftwareTimer.timer.schedule))
        self.instance.ip = "0.0.0.0"
        self.instance.off()
        self.assertIn(self.instance.name, str(SoftwareTimer.timer.schedule))
        SoftwareTimer.timer.cancel(self.instance.name)
        self.instance.ip = config["mock_receiver"]["ip"]

        # Simulate error due to non-JSON response, instance should be disabled
        self.instance.port = config["mock_receiver"]["error_port"]
        self.instance.off()
        self.assertFalse(self.instance.enabled)
        self.instance.enable()

    def test_13_network_errors(self):
        # Change to invalid IP to simulate failed connection, confirm send returns False
        self.instance.ip = "0.0.0.0"
        self.assertFalse(self.instance.send(1))
        self.instance.ip = config["mock_receiver"]["ip"]

        # Change port to error port (mock receiver returns error for all requests on this port)
        # Confirm send method returns False
        self.instance.port = config["mock_receiver"]["error_port"]
        self.instance.send(1)
        self.assertFalse(self.instance.enabled)
        self.instance.port = config["mock_receiver"]["port"]
