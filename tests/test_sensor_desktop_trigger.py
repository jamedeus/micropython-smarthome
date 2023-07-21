import json
import unittest
import uasyncio as asyncio
from Group import Group
from Desktop_target import Desktop_target
from Desktop_trigger import Desktop_trigger

# Read mock API receiver address
with open('config.json', 'r') as file:
    config = json.load(file)

# Expected return value of get_attributes method just after instantiation
expected_attributes = {
    'ip': config['mock_receiver']['ip'],
    'port': config['mock_receiver']['port'],
    'nickname': 'sensor1',
    'current': None,
    'desktop_target': 'device1',
    'enabled': True,
    'group': 'group1',
    'rule_queue': [],
    'name': 'sensor1',
    'default_rule': 'enabled',
    '_type': 'desktop',
    'current_rule': None,
    'scheduled_rule': None,
    'targets': ['device1']
}


class TestDesktopTrigger(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Get mock command receiver address
        ip = config["mock_receiver"]["ip"]
        port = config["mock_receiver"]["port"]

        # Create test instance, target instance, group instance
        cls.target = Desktop_target("device1", "device1", "desktop", "enabled", ip, port)
        cls.instance = Desktop_trigger("sensor1", "sensor1", "desktop", "enabled", [cls.target], ip, port)
        group = Group('group1', [cls.instance])
        cls.instance.group = group

    def test_01_initial_state(self):
        self.assertIsInstance(self.instance, Desktop_trigger)
        self.assertTrue(self.instance.enabled)

    def test_02_get_attributes(self):
        attributes = self.instance.get_attributes()
        self.assertEqual(attributes, expected_attributes)

    def test_03_rule_validation_valid(self):
        self.assertEqual(self.instance.rule_validator("enabled"), "enabled")
        self.assertEqual(self.instance.rule_validator("Enabled"), "enabled")
        self.assertEqual(self.instance.rule_validator("ENABLED"), "enabled")
        self.assertEqual(self.instance.rule_validator("disabled"), "disabled")
        self.assertEqual(self.instance.rule_validator("Disabled"), "disabled")

    def test_04_rule_validation_invalid(self):
        self.assertFalse(self.instance.rule_validator(True))
        self.assertFalse(self.instance.rule_validator(None))
        self.assertFalse(self.instance.rule_validator("string"))
        self.assertFalse(self.instance.rule_validator(42))
        self.assertFalse(self.instance.rule_validator(["Enabled"]))
        self.assertFalse(self.instance.rule_validator({"Enabled": "Enabled"}))

    def test_05_rule_change(self):
        self.assertTrue(self.instance.set_rule("Enabled"))
        self.assertEqual(self.instance.current_rule, 'enabled')
        self.assertTrue(self.instance.enabled)

        self.assertTrue(self.instance.set_rule("Disabled"))
        self.assertEqual(self.instance.current_rule, 'disabled')
        self.assertFalse(self.instance.enabled)

    def test_06_enable_disable(self):
        self.instance.disable()
        self.assertFalse(self.instance.enabled)
        self.instance.enable()
        self.assertTrue(self.instance.enabled)

    def test_07_get_idle_time(self):
        idle_time = self.instance.get_idle_time()
        self.assertIsInstance(idle_time, dict)
        self.assertIsInstance(int(idle_time["idle_time"]), int)

    def test_08_get_monitor_state(self):
        state = self.instance.get_monitor_state()
        self.assertIsInstance(state, str)
        self.assertIn(state, ['On', 'Off', 'Disabled'])

    def test_09_trigger(self):
        # Ensure not already triggered to avoid false positive
        self.instance.current = "Off"
        self.assertFalse(self.instance.condition_met())
        # Trigger, condition should now be met
        self.assertTrue(self.instance.trigger())
        self.assertTrue(self.instance.condition_met())

    def test_10_network_errors(self):
        # Change port to error port (mock receiver returns error for all requests on this port)
        self.instance.port = config["mock_receiver"]["error_port"]

        # Confirm that network error in get_idle_time() disables instance
        self.assertTrue(self.instance.enabled)
        self.assertFalse(self.instance.get_idle_time())
        self.assertFalse(self.instance.enabled)
        self.instance.enable()

        # Confirm that invalid json response in get_monitor_state() disables instance
        self.assertTrue(self.instance.enabled)
        self.assertFalse(self.instance.get_monitor_state())
        self.assertFalse(self.instance.enabled)
        self.instance.enable()

        # Revert port, change to invalid IP to simulate failed network request
        self.instance.port = config["mock_receiver"]["error_port"]
        self.instance.ip = "0.0.0."

        # Confirm get_monitor_state returns False when network error encountered
        self.assertFalse(self.instance.get_monitor_state())
        self.instance.ip = config["mock_receiver"]["ip"]

    def test_11_exit_monitor_loop_when_disabled(self):
        # Disable instance, confirm monitor coro returns False (end of loop)
        self.instance.disable()
        self.assertFalse(asyncio.run(self.instance.monitor()))
