import sys
import unittest
from Group import Group
from Sensor import Sensor
from cpython_only import cpython_only

# Import dependencies for tests that only run in mocked environment
if sys.implementation.name == 'cpython':
    from unittest.mock import patch


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

    # Original bug: If set_rule was called with "enabled" the apply_new_rule
    # method would set current_rule to default_rule instead of scheduled_rule.
    def test_11_regression_enable_with_rule_change_ignores_scheduled_rule(self):
        # Starting conditions
        self.instance.disable()
        self.instance.scheduled_rule = 25
        self.instance.default_rule = 50
        self.assertFalse(self.instance.enabled)

        # Enable device by calling set_rule method
        self.assertTrue(self.instance.set_rule("enabled"))

        # Confirm switched to scheduled_rule, not default_rule
        self.assertEqual(self.instance.current_rule, 25)

    # Original bug: If current_rule == "disabled" when enable method is called
    # it calls set_rule to replace "disabled" with a usable rule. If the new
    # rule is "enabled" the apply_new_rule method called enable again without
    # checking if the sensor was already enabled. This caused the refresh_group
    # method to be called twice in a row (each enable call) instead of once.
    # The apply_new_rule method now only calls enable if the sensor is disabled
    # (ensures enable and refresh_group are only called once).
    @cpython_only
    def test_12_regression_enable_method_called_twice(self):
        # Set current_rule to "disabled", confirm disabled
        self.instance.set_rule("disabled")
        self.assertFalse(self.instance.enabled)

        # Set default and scheduled rule to "enabled" (when enable method is
        # called current_rule will be replaced with "enabled")
        self.instance.default_rule = "enabled"
        self.instance.scheduled_rule = "enabled"

        with patch.object(self.instance, 'refresh_group') as mock_refresh:
            # Call enable method
            self.instance.enable()

            # Confirm instance is enabled, rule is "enabled"
            self.assertTrue(self.instance.enabled)
            self.assertEqual(self.instance.current_rule, "enabled")

            # Confirm refresh_group was only called once
            mock_refresh.assert_called_once()

    # Original bug: If current_rule == "disabled" when enable method is called
    # it calls set_rule to replace "disabled" with a usable rule. By default it
    # uses scheduled_rule, but if this is also "disabled" it uses default_rule.
    # If default_rule was also "disabled" the apply_new_rule method would call
    # disable, making it impossible to enable the device until scheduled_rule
    # changed to something else. The enable method now checks default_rule and
    # only calls set_rule if it is not "disabled".
    def test_13_regression_enable_method_breaks_if_default_rule_is_disabled(self):
        # Set current_rule to "disabled", confirm disabled
        self.instance.set_rule("disabled")
        self.assertFalse(self.instance.enabled)

        # Set default and scheduled rule to "disabled" (before fix the enable
        # method would blindly call self.set_rule(self.default_rule)) without
        # checking if default_rule was also "disabled")
        self.instance.default_rule = "disabled"
        self.instance.scheduled_rule = "disabled"

        # Call enable method, confirm sensor is enabled (did not call disable)
        self.instance.enable()
        self.assertTrue(self.instance.enabled)
