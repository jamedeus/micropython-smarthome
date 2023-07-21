import json
import unittest
from Relay import Relay

# Read mock API receiver address
with open('config.json', 'r') as file:
    config = json.load(file)

# IP and port of mock API receiver instance
mock_address = f"{config['mock_receiver']['ip']}:{config['mock_receiver']['port']}"

# Expected return value of get_attributes method just after instantiation
expected_attributes = {
    'triggered_by': [],
    'nickname': 'device1',
    'ip': mock_address,
    'enabled': True,
    'rule_queue': [],
    'state': None,
    'default_rule': 'enabled',
    'name': 'device1',
    '_type': 'relay',
    'scheduled_rule': None,
    'current_rule': None
}


class TestRelay(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.instance = Relay("device1", "device1", "relay", "enabled", mock_address)

    def test_01_initial_state(self):
        self.assertIsInstance(self.instance, Relay)
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

    def test_09_turn_on(self):
        self.assertTrue(self.instance.send(1))
        self.assertEqual(self.instance.check_state(), 'ON')

    def test_10_turn_off(self):
        self.assertTrue(self.instance.send(0))
        self.assertEqual(self.instance.check_state(), 'OFF')

    def test_11_turn_on_while_disabled(self):
        self.instance.disable()
        self.assertTrue(self.instance.send(1))
        self.instance.enable()

    def test_12_network_errors(self):
        # Instantiate with invalid IP, confirm send method returns False
        test = Relay("device1", "device1", "relay", "enabled", "0.0.0.")
        self.assertFalse(test.send(0))
        self.assertFalse(test.send(1))
        self.assertEqual(test.check_state(), "Network Error")

        # Change port to error port (mock receiver returns error for all requests on this port)
        # Confirm send method returns False
        self.instance.ip = f"{config['mock_receiver']['ip']}:{config['mock_receiver']['error_port']}"
        self.assertFalse(self.instance.send(1))
