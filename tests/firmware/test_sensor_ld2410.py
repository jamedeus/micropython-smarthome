import unittest
from machine import Pin
import SoftwareTimer
from Group import Group
from Ld2410 import Ld2410
from cpython_only import cpython_only

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
    '_type': 'ld2410',
    'current_rule': None,
    'scheduled_rule': None
}


# Subclass Group to detect when refresh method called
class MockGroup(Group):
    def __init__(self, name, sensors):
        super().__init__(name, sensors)

        self.refresh_called = False

    def refresh(self, arg=None):
        self.refresh_called = True
        super().refresh()


class TestLd2410Sensor(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.instance = Ld2410("sensor1", "sensor1", "ld2410", None, [], 15)
        cls.group = MockGroup("group1", [cls.instance])
        cls.instance.group = cls.group

    def test_01_initial_state(self):
        # Confirm expected attributes just after instantiation
        self.assertIsInstance(self.instance, Ld2410)
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
        self.assertFalse(self.instance.rule_validator("NaN"))

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

        # Simulate sensor triggered by hware interrupt
        self.instance.trigger()
        # SoftwareTimer queue should now contain entry containing sensor's name attribute
        self.assertIn(self.instance.name, str(SoftwareTimer.timer.schedule))
        # Motion attribute should be True
        self.assertTrue(self.instance.motion)
        # Group.refresh should have been called
        self.assertTrue(self.group.refresh_called)
        self.group.refresh_called = False

        # Simulate reset timer expiring, motion should now be False
        self.instance.reset_timer()
        self.assertFalse(self.instance.motion)
        # Group.refresh should be called again
        self.assertTrue(self.group.refresh_called)
        self.group.refresh_called = False

        # Set rule to None, cancel previous timer to avoid false positive
        self.instance.set_rule(None)
        SoftwareTimer.timer.cancel(self.instance.name)
        # Simulate sensor triggered by hware interrupt
        self.instance.trigger()
        # Queue should NOT contain entry for motion sensor (rule is None)
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

        # Attempt to increment by NaN, confirm error, confirm rule does not change
        response = self.instance.increment_rule("NaN")
        self.assertEqual(response, {'ERROR': 'Invalid argument nan'})
        self.assertEqual(self.instance.current_rule, 6)

        # Set rule to disabled, confirm correct error
        self.instance.set_rule('Disabled')
        self.assertEqual(
            self.instance.increment_rule(1),
            {"ERROR": "Unable to increment current rule (disabled)"}
        )

    def test_10_next_rule(self):
        # Ensure enabled, set motion to True, confirm no reset timer in queue
        self.instance.enable()
        self.instance.motion = True
        self.assertTrue(self.instance.name not in str(SoftwareTimer.timer.schedule))

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

    def test_11_prevent_invalid_default_rule(self):
        with self.assertRaises(AttributeError):
            Ld2410("sensor1", "sensor1", "pir", "disabled", [], 15)

        with self.assertRaises(AttributeError):
            Ld2410("sensor1", "sensor1", "pir", "enabled", [], 15)

    @cpython_only
    def test_12_pin_interrupt_with_reset_timer(self):
        # Set rule to 5, motion False, targets off, stop reset timer
        self.instance.current_rule = 5
        self.instance.motion = False
        self.group.refresh_called = False
        SoftwareTimer.timer.cancel(self.instance.name)

        # Simulate interrupt triggered by rising pin
        self.instance.sensor.pin_state = 1
        self.instance.pin_interrupt()

        # Confirm motion detected, targets turned on, reset timer running
        self.assertTrue(self.instance.motion)
        self.assertTrue(self.group.refresh_called)
        self.assertIn(self.instance.name, str(SoftwareTimer.timer.schedule))

        # Simulate interrupt triggered by falling pin
        self.instance.sensor.pin_state = 0
        self.instance.pin_interrupt()

        # Confirm nothing changed (targets stay on until reset timer expires)
        self.assertTrue(self.instance.motion)
        self.assertIn(self.instance.name, str(SoftwareTimer.timer.schedule))
        self.assertTrue(self.group.refresh_called)

    @cpython_only
    def test_13_pin_interrupt_no_reset_timer(self):
        # Set rule to 0 (disable reset timer)
        self.instance.current_rule = 0
        # Set motion False, targets off, stop reset timer
        self.instance.motion = False
        self.group.refresh_called = False
        SoftwareTimer.timer.cancel(self.instance.name)

        # Simulate interrupt triggered by rising pin
        self.instance.sensor.pin_state = 1
        self.instance.pin_interrupt()

        # Confirm motion detected, targets turned on, reset timer NOT running
        self.assertTrue(self.instance.motion)
        self.assertTrue(self.group.refresh_called)
        self.assertTrue(self.instance.name not in str(SoftwareTimer.timer.schedule))

        # Simulate interrupt triggered by falling pin
        self.group.refresh_called = False
        self.instance.sensor.pin_state = 0
        self.instance.pin_interrupt()

        # Confirm motion not detected, targets turned off
        self.assertFalse(self.instance.motion)
        self.assertTrue(self.group.refresh_called)

    @cpython_only
    def test_14_reset_timer_motion_still_detected(self):
        # Set rule to 5, confirm no reset timer running
        self.instance.current_rule = 5
        self.assertTrue(self.instance.name not in str(SoftwareTimer.timer.schedule))

        # Simulate sensor detecting motion
        self.instance.sensor.pin_state = 1
        self.instance.motion = True

        # Simulate reset timer expiring while still detecting motion (only
        # happens if detected for whole duration, otherwise resets each time
        # motion stops and restarts and reset_timer is never called)
        self.instance.reset_timer()

        # Confirm reset timer was restarted when old timer expired (prevent
        # getting stuck ON if timer expires before motion stops)
        self.assertIn(self.instance.name, str(SoftwareTimer.timer.schedule))

        # Confirm motion is still True
        self.assertTrue(self.instance.motion)
