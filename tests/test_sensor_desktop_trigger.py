import json
import unittest
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
    'desktop_target': None,
    'enabled': True,
    'rule_queue': [],
    'name': 'sensor1',
    'default_rule': 'enabled',
    '_type': 'desktop',
    'current_rule': None,
    'scheduled_rule': None,
    'targets': []
}


class TestDesktopTrigger(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        ip = config["mock_receiver"]["ip"]
        port = config["mock_receiver"]["port"]
        cls.instance = Desktop_trigger("sensor1", "sensor1", "desktop", "enabled", [], ip, port)

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
