import unittest
from Group import Group
from Sensor import Sensor


# Subclass Group to detect when refresh method called
class MockGroup(Group):
    def __init__(self, name, sensors):
        super().__init__(name, sensors)

        self.refresh_called = False

    def refresh(self, arg=None):
        self.refresh_called = True


class TestSensor(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Create test instance, add rule to queue
        cls.instance = Sensor("sensor1", "Test", "sensor", True, "enabled", "enabled", [])
        cls.instance.rule_queue = ["disabled"]

        # Create mock group
        cls.group = MockGroup("group1", [cls.instance])
        cls.instance.group = cls.group

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

        # Ensure Group.refresh not called
        self.group.refresh_called = False

        # Enable, confirm rule changes to scheduled_rule, confirm Group.refresh called
        self.instance.enable()
        self.assertTrue(self.instance.enabled)
        self.assertEqual(self.instance.current_rule, self.instance.scheduled_rule)
        self.assertTrue(self.group.refresh_called)

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

        # Ensure Group.refresh not called
        self.group.refresh_called = False

        # Disable, confirm disabled, confirm Group.refresh called
        self.instance.disable()
        self.assertFalse(self.instance.enabled)
        self.assertTrue(self.group.refresh_called)

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

    def test_07_disable_by_rule_change(self):
        # Set rule to disabled, confirm disabled
        self.instance.enable()
        self.instance.set_rule("Disabled")
        self.assertFalse(self.instance.enabled)

    def test_08_enable_by_rule_change(self):
        # Set rule to enabled, confirm enabled
        self.assertFalse(self.instance.enabled)
        self.instance.set_rule("Enabled")
        self.assertTrue(self.instance.enabled)

    def test_09_next_rule(self):
        # Confirm current_rule doesn't match expected new rule
        self.instance.set_rule('enabled')
        self.assertNotEqual(self.instance.current_rule, "disabled")

        # Move to next rule, confirm correct rule
        self.instance.next_rule()
        self.assertEqual(self.instance.current_rule, "disabled")

    def test_10_refresh_group(self):
        # Ensure Group.refresh not called
        self.group.refresh_called = False

        # Call method, confirm Group.refresh called
        self.instance.refresh_group()
        self.assertTrue(self.group.refresh_called)
