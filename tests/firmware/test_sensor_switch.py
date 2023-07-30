import unittest
from Switch import Switch

# Expected return value of get_attributes method just after instantiation
expected_attributes = {
    'rule_queue': [],
    'enabled': True,
    'default_rule': 'enabled',
    'name': 'sensor1',
    '_type': 'switch',
    'nickname': 'sensor1',
    'current_rule': None,
    'scheduled_rule': None,
    'targets': []
}


class TestSwitch(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.instance = Switch("sensor1", "sensor1", "switch", "enabled", [], 19)

    def test_01_initial_state(self):
        self.assertIsInstance(self.instance, Switch)
        self.assertTrue(self.instance.enabled)

    def test_02_get_attributes(self):
        attributes = self.instance.get_attributes()
        self.assertEqual(attributes, expected_attributes)

    def test_03_trigger(self):
        # Should not be able to trigger this sensor type
        self.assertFalse(self.instance.trigger())

    def test_04_condition_met(self):
        self.assertFalse(self.instance.condition_met())

        # Mock env: simulate turnned on (conditional prevents fail on baremetal)
        self.instance.switch.value(1)
        if self.instance.switch.value():
            self.assertTrue(self.instance.condition_met())
