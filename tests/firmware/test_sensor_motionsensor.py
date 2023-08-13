import unittest
from machine import Pin
import SoftwareTimer
from Group import Group
from MotionSensor import MotionSensor

# Expected return value of get_attributes method just after instantiation
expected_attributes = {
    'targets': [],
    'nickname': 'sensor1',
    'motion': False,
    'enabled': True,
    'group': 'group1',
    'rule_queue': [],
    'name': 'sensor1',
    'default_rule': None,
    '_type': 'pir',
    'current_rule': None,
    'scheduled_rule': None
}


# Subclass Group to detect when refresh method called
class MockGroup(Group):
    def __init__(self, name, sensors):
        super().__init__(name, sensors)

        self.refresh_called = False

    def refresh(self):
        self.refresh_called = True
        super().refresh()


class TestMotionSensor(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.instance = MotionSensor("sensor1", "sensor1", "pir", None, [], 15)
        cls.group = MockGroup("group1", [cls.instance])
        cls.instance.group = cls.group

    def test_01_initial_state(self):
        # Confirm expected attributes just after instantiation
        self.assertIsInstance(self.instance, MotionSensor)
        self.assertIsInstance(self.instance.sensor, Pin)
        self.assertTrue(self.instance.enabled)
        self.assertFalse(self.instance.motion)
        self.assertEqual(self.instance.sensor.value(), 0)

    def test_02_get_attributes(self):
        # Confirm expected attributes dict just after instantiation
        attributes = self.instance.get_attributes()
        self.assertEqual(attributes, expected_attributes)

    def test_03_rule_validation_valid(self):
        # Should accept int and float in addition to enabled and disabled
        self.assertEqual(self.instance.rule_validator(5), 5.0)
        self.assertEqual(self.instance.rule_validator(0.5), 0.5)
        self.assertEqual(self.instance.rule_validator("0.5"), 0.5)
        self.assertEqual(self.instance.rule_validator("Disabled"), "disabled")
        # Should accept None but cast to 0.0
        self.assertEqual(self.instance.rule_validator(None), 0.0)

    def test_04_rule_validation_invalid(self):
        # Should reject all other rules
        self.assertFalse(self.instance.rule_validator(True))
        self.assertFalse(self.instance.rule_validator("string"))
        self.assertFalse(self.instance.rule_validator([10]))
        self.assertFalse(self.instance.rule_validator({5: 5}))
        self.assertFalse(self.instance.rule_validator("None"))

    def test_05_enable_disable(self):
        # Disable, confirm disabled
        self.instance.disable()
        self.assertFalse(self.instance.enabled)

        # Set motion to True, enable, confirm flips to False
        self.instance.motion = True
        self.instance.enable()
        self.assertTrue(self.instance.enabled)
        self.assertFalse(self.instance.motion)

    def test_06_reset_timer(self):
        # Make sure rule isn't None (no timer set), Group.refresh not called
        self.instance.set_rule(1)
        self.group.refresh_called = False

        # Call method triggered by hware interrupt
        self.instance.motion_detected()
        # SoftwareTimer queue should now contain entry containing sensor's name attribute
        self.assertIn(self.instance.name, str(SoftwareTimer.timer.schedule))
        # Motion attribute should be True
        self.assertTrue(self.instance.motion)
        # Group.refresh should have been called
        self.assertTrue(self.group.refresh_called)
        self.group.refresh_called = False

        # Simulate reset timer expiring, motion should now be False
        self.instance.resetTimer()
        self.assertFalse(self.instance.motion)
        # Group.refresh should be called again
        self.assertTrue(self.group.refresh_called)
        self.group.refresh_called = False

        # Set rule to None, cancel previous timer to avoid false positive
        self.instance.set_rule(None)
        SoftwareTimer.timer.cancel(self.instance.name)
        # Call method triggered by hware interrupt
        self.instance.motion_detected()
        # Queue should NOT contain entry for motion sensor
        self.assertTrue(self.instance.name not in str(SoftwareTimer.timer.schedule))

    def test_07_trigger(self):
        # Ensure not already tiggered to avoid false positive
        self.instance.motion = False
        # Trigger, condition should now be met
        self.assertTrue(self.instance.trigger())
        self.assertTrue(self.instance.condition_met())

    def test_08_condition_met(self):
        # Confirm condition_met returns self.motion
        self.instance.motion = True
        self.assertTrue(self.instance.condition_met())
        self.instance.motion = False
        self.assertFalse(self.instance.condition_met())

    def test_09_increment_rule(self):
        # Set rule to 5, increment by 1, confirm rule is now 6
        self.instance.current_rule = 5
        self.assertTrue(self.instance.increment_rule(1))
        self.assertEqual(self.instance.current_rule, 6)

        # Set rule to disabled, confirm correct error
        self.instance.set_rule('Disabled')
        self.assertEqual(
            self.instance.increment_rule(1),
            {"ERROR": "Unable to increment current rule (disabled)"}
        )

    def test_10_next_rule(self):
        # Ensure enabled, confirm no reset timer in queu, set motion to True
        self.instance.enable()
        self.assertTrue(self.instance.name not in str(SoftwareTimer.timer.schedule))
        self.instance.trigger()

        # Add rules to queue, first should trigger reset timer, second should not
        self.instance.rule_queue = [5, 'disabled']

        # Move to next rule, confirm timer created, confirm rule set
        self.instance.next_rule()
        self.assertTrue(self.instance.motion)
        self.assertEqual(self.instance.current_rule, 5)
        self.assertIn(self.instance.name, str(SoftwareTimer.timer.schedule))
        SoftwareTimer.timer.cancel(self.instance.name)

        # Set to disabled, confirm rule set, confirm no timer created
        self.instance.next_rule()
        self.assertEqual(self.instance.current_rule, 'disabled')
        self.assertTrue(self.instance.name not in str(SoftwareTimer.timer.schedule))

    # Original bug: Some sensors would crash or behave unexpectedly if default_rule was "enabled" or "disabled"
    # in various situations. These classes now raise exception in init method to prevent this.
    # It should no longer be possible to instantiate with invalid default_rule.
    def test_11_regression_invalid_default_rule(self):
        with self.assertRaises(AttributeError):
            MotionSensor("sensor1", "sensor1", "pir", "disabled", [], 15)

        with self.assertRaises(AttributeError):
            MotionSensor("sensor1", "sensor1", "pir", "enabled", [], 15)

    # Original bug: increment_rule cast argument to float inside try/except, relying
    # on exception to detect invalid argument. Since NaN is a valid float no exception
    # was raised and rule changed to NaN, leading to exception when motion detected.
    def test_12_regression_increment_by_nan(self):
        # Starting condition
        self.instance.set_rule(5)

        # Attempt to increment by NaN, confirm error, confirm rule does not change
        response = self.instance.increment_rule("NaN")
        self.assertEqual(response, {'ERROR': 'Invalid argument nan'})
        self.assertEqual(self.instance.current_rule, 5.0)

    # Original bug: validator accepted any argument that could be cast to float. Since
    # NaN is a valid float it was accepted, leading to a broken reset timer. Now rejects.
    def test_13_regression_validator_accepts_nan(self):
        # Attempt to set rule to NaN, should reject
        self.assertFalse(self.instance.set_rule("NaN"))
