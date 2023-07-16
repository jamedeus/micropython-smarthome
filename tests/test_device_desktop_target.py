import unittest
from Desktop_target import Desktop_target

# Expected return value of get_attributes method just after instantiation
expected_attributes = {
    'triggered_by': [],
    'nickname': 'device1',
    'ip': '192.168.1.216',
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

    def __dir__(self):
        return [
            "test_initial_state",
            "test_get_attributes",
            "test_rule_validation_valid",
            "test_rule_validation_invalid",
            "test_rule_change",
            "test_enable_disable",
            "test_disable_by_rule_change",
            "test_enable_by_rule_change",
            "test_turn_off",
            "test_turn_on"
        ]

    @classmethod
    def setUpClass(cls):
        cls.instance = Desktop_target("device1", "device1", "desktop", "enabled", "192.168.1.216")

    def test_initial_state(self):
        self.assertIsInstance(self.instance, Desktop_target)
        self.assertTrue(self.instance.enabled)

    def test_get_attributes(self):
        attributes = self.instance.get_attributes()
        self.assertEqual(attributes, expected_attributes)

    def test_rule_validation_valid(self):
        self.assertEqual(self.instance.rule_validator("Disabled"), "disabled")
        self.assertEqual(self.instance.rule_validator("DISABLED"), "disabled")
        self.assertEqual(self.instance.rule_validator("Enabled"), "enabled")
        self.assertEqual(self.instance.rule_validator("enabled"), "enabled")

    def test_rule_validation_invalid(self):
        self.assertFalse(self.instance.rule_validator(True))
        self.assertFalse(self.instance.rule_validator(None))
        self.assertFalse(self.instance.rule_validator("string"))
        self.assertFalse(self.instance.rule_validator(42))
        self.assertFalse(self.instance.rule_validator("on"))
        self.assertFalse(self.instance.rule_validator("off"))
        self.assertFalse(self.instance.rule_validator(["enabled"]))
        self.assertFalse(self.instance.rule_validator({"disabled": "disabled"}))

    def test_rule_change(self):
        self.assertTrue(self.instance.set_rule("disabled"))
        self.assertEqual(self.instance.current_rule, 'disabled')
        self.assertTrue(self.instance.set_rule("enabled"))
        self.assertEqual(self.instance.current_rule, 'enabled')

    def test_enable_disable(self):
        self.instance.disable()
        self.assertFalse(self.instance.enabled)
        self.instance.enable()
        self.assertTrue(self.instance.enabled)

    def test_disable_by_rule_change(self):
        self.instance.set_rule("Disabled")
        self.assertFalse(self.instance.enabled)

    def test_enable_by_rule_change(self):
        self.instance.set_rule("enabled")
        self.assertTrue(self.instance.enabled)

    def test_turn_off(self):
        self.assertTrue(self.instance.send(0))

    def test_turn_on(self):
        self.assertTrue(self.instance.send(1))

    # TODO Add method that checks current state, write tests confirming correct state
