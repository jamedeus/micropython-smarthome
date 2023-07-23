import unittest
from Sensor import Sensor


class TestSensor(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Create test instance, add rule to queue
        cls.instance = Sensor("sensor1", "Test", "sensor", True, "enabled", "enabled", [])
        cls.instance.rule_queue = ["disabled"]

    def test_01_initial_state(self):
        # Confirm expected attributes just after instantiation
        self.assertIsInstance(self.instance, Sensor)
        self.assertEqual(self.instance.name, "sensor1")
        self.assertEqual(self.instance.nickname, "Test")
        self.assertTrue(self.instance.enabled)
        self.assertEqual(self.instance.current_rule, "enabled")
        self.assertEqual(self.instance.scheduled_rule, "enabled")
        self.assertEqual(self.instance.default_rule, "enabled")
        self.assertEqual(self.instance.targets, [])

    def test_02_enable(self):
        # Set rule to disabled, confirm disabled
        self.instance.set_rule('disabled')
        self.assertFalse(self.instance.enabled)

        # Enable, confirm rule changes to scheduled_rule
        self.instance.enable()
        self.assertTrue(self.instance.enabled)
        self.assertEqual(self.instance.current_rule, self.instance.scheduled_rule)

    def test_03_enable_with_invalid_schedule_rule(self):
        # Set both current and scheduled rules disabled
        self.instance.set_rule('disabled')
        self.instance.scheduled_rule = 'disabled'
        self.assertFalse(self.instance.enabled)

        # Enable, confirm rule falls back to default_rule
        self.instance.enable()
        self.assertTrue(self.instance.enabled)
        self.assertEqual(self.instance.current_rule, self.instance.default_rule)

    def test_03_disable(self):
        # Enable sensor
        self.instance.enable()
        self.assertTrue(self.instance.enabled)

        # Disable, confirm disabled
        self.instance.disable()
        self.assertFalse(self.instance.enabled)

    def test_04_rule_validation_valid(self):
        # Should accept enabled and disabled, case insensitive
        self.assertEqual(self.instance.rule_validator("enabled"), "enabled")
        self.assertEqual(self.instance.rule_validator("Enabled"), "enabled")
        self.assertEqual(self.instance.rule_validator("ENABLED"), "enabled")
        self.assertEqual(self.instance.rule_validator("disabled"), "disabled")
        self.assertEqual(self.instance.rule_validator("Disabled"), "disabled")

    def test_05_rule_validation_invalid(self):
        # Should reject all rules that are not enabled or disabled
        self.assertFalse(self.instance.rule_validator(True))
        self.assertFalse(self.instance.rule_validator(None))
        self.assertFalse(self.instance.rule_validator("string"))
        self.assertFalse(self.instance.rule_validator(42))
        self.assertFalse(self.instance.rule_validator(["Enabled"]))
        self.assertFalse(self.instance.rule_validator({"Enabled": "Enabled"}))

    def test_06_set_rule(self):
        # Set rule, confirm rule changed
        self.instance.current_rule = "disabled"
        self.assertTrue(self.instance.set_rule("enabled"))
        self.assertEqual(self.instance.current_rule, "enabled")

        # Confirm rejects invalid rule
        self.assertFalse(self.instance.set_rule('string'))
        self.assertEqual(self.instance.current_rule, "enabled")

    def test_07_next_rule(self):
        # Confirm current_rule doesn't match expected new rule
        self.instance.set_rule('enabled')
        self.assertNotEqual(self.instance.current_rule, "disabled")

        # Move to next rule, confirm correct rule
        self.instance.next_rule()
        self.assertEqual(self.instance.current_rule, "disabled")
