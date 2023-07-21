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
        self.assertFalse(self.instance.rule_validator(["on"]))
        self.assertFalse(self.instance.rule_validator({"on": "on"}))
        self.assertFalse(self.instance.rule_validator("On"))
        self.assertFalse(self.instance.rule_validator("ON"))

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

    def test_07_trigger(self):
        # Should not be able to trigger this sensor type
        self.assertFalse(self.instance.trigger())

    def test_08_condition_met(self):
        self.assertFalse(self.instance.condition_met())

        # Mock env: simulate turnned on (conditional prevents fail on baremetal)
        self.instance.switch.value(1)
        if self.instance.switch.value():
            self.assertTrue(self.instance.condition_met())
