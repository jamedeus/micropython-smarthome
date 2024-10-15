import asyncio
import unittest
from machine import Pin
import SoftwareTimer
from Group import Group
from MotionSensor import MotionSensor
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
    '_type': 'pir',
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


class TestMotionSensorSensor(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.instance = MotionSensor("sensor1", "sensor1", "pir", None, [], 15)
        cls.group = MockGroup("group1", [cls.instance])
        cls.instance.group = cls.group

    def setUp(self):
        # Ensure no reset timer from previous test in queue
        SoftwareTimer.timer.cancel('sensor1')
        asyncio.run(asyncio.sleep_ms(10))

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

    def test_04_rule_validation_invalid(self):
        # Should reject all other rules
        self.assertFalse(self.instance.rule_validator(True))
        self.assertFalse(self.instance.rule_validator("string"))
        self.assertFalse(self.instance.rule_validator([10]))
        self.assertFalse(self.instance.rule_validator({5: 5}))
        self.assertFalse(self.instance.rule_validator(None))
        self.assertFalse(self.instance.rule_validator("None"))
        self.assertFalse(self.instance.rule_validator("NaN"))

    def test_05_enable_disable(self):
        # Simulate active reset timer
        SoftwareTimer.timer.create(1000, self.instance.reset_timer, self.instance.name)
        asyncio.run(asyncio.sleep_ms(100))
        self.assertTrue(self.instance.name in str(SoftwareTimer.timer.schedule))

        # Disable, confirm disabled
        self.instance.disable()
        self.assertFalse(self.instance.enabled)

        # Confirm reset timer was removed from SoftwareTimer queue
        asyncio.run(asyncio.sleep_ms(100))
        self.assertTrue(self.instance.name not in str(SoftwareTimer.timer.schedule))

        # Set motion to True, enable, confirm flips to False
        self.instance.motion = True
        self.instance.enable()
        self.assertTrue(self.instance.enabled)
        self.assertFalse(self.instance.motion)

    def test_06_reset_timer(self):
        # Make sure rule isn't 0 (no timer set), Group.refresh not called
        self.instance.set_rule(1)
        self.group.refresh_called = False

        # Confirm no reset timer in SoftwareTimer queue
        self.assertTrue(self.instance.name not in str(SoftwareTimer.timer.schedule))

        # Simulate sensor triggered by hware interrupt
        self.instance.trigger()
        # Yield to let SoftwareTimer coroutine create reset timer
        asyncio.run(asyncio.sleep_ms(10))

        # SoftwareTimer queue should now contain entry containing sensor's name attribute
        self.assertIn(self.instance.name, str(SoftwareTimer.timer.schedule))
        # Motion attribute should be True
        self.assertTrue(self.instance.motion)
        # Group.refresh should have been called
        self.assertTrue(self.group.refresh_called)
        self.group.refresh_called = False

        # Simulate reset timer expiring, motion should now be False
        self.instance.reset_timer()
        # Yield to let SoftwareTimer coroutine create reset timer (reset_timer
        # method may call start_reset_timer if motion still detected)
        asyncio.run(asyncio.sleep_ms(10))
        self.assertFalse(self.instance.motion)
        # Group.refresh should be called again
        self.assertTrue(self.group.refresh_called)
        self.group.refresh_called = False

        # Set rule to 0, cancel previous timer to avoid false positive
        self.instance.set_rule(0)
        SoftwareTimer.timer.cancel(self.instance.name)
        # Simulate sensor triggered by hware interrupt
        self.instance.trigger()
        # Yield to let SoftwareTimer coroutines cancel old reset timer, create
        # new reset timer (should not create new since rule is 0)
        asyncio.run(asyncio.sleep_ms(10))
        # Queue should NOT contain entry for motion sensor (rule is 0)
        self.assertTrue(self.instance.name not in str(SoftwareTimer.timer.schedule))

    def test_07_trigger(self):
        # Ensure not already triggered to avoid false positive
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
        # Ensure enabled, set motion to True, confirm no reset timer in queue
        self.instance.enable()
        self.instance.motion = True
        self.assertTrue(self.instance.name not in str(SoftwareTimer.timer.schedule))

        # Add rules to queue, first should trigger reset timer, second should not
        self.instance.rule_queue = [5, 'disabled']

        # Move to next rule, confirm rule set, confirm timer created
        self.instance.next_rule()
        self.assertTrue(self.instance.motion)
        self.assertEqual(self.instance.current_rule, 5)
        # Yield to let SoftwareTimer coroutine create reset timer
        asyncio.run(asyncio.sleep_ms(10))
        self.assertIn(self.instance.name, str(SoftwareTimer.timer.schedule))
        SoftwareTimer.timer.cancel(self.instance.name)

        # Set to disabled, confirm rule set, confirm no timer created
        self.instance.next_rule()
        # Yield to let SoftwareTimer coroutine create reset timer
        asyncio.run(asyncio.sleep_ms(10))
        self.assertEqual(self.instance.current_rule, 'disabled')
        self.assertTrue(self.instance.name not in str(SoftwareTimer.timer.schedule))

    @cpython_only
    def test_11_pin_interrupt_with_reset_timer(self):
        # Set rule to 5, motion False, targets off, stop reset timer
        self.instance.current_rule = 5
        self.instance.motion = False
        self.group.refresh_called = False
        SoftwareTimer.timer.cancel(self.instance.name)
        asyncio.run(asyncio.sleep_ms(10))

        # Simulate interrupt triggered by rising pin
        self.instance.sensor.pin_state = 1
        self.instance.pin_interrupt()
        # Yield to let SoftwareTimer coroutine create reset timer
        asyncio.run(asyncio.sleep_ms(10))

        # Confirm motion detected, targets turned on, reset timer running
        self.assertTrue(self.instance.motion)
        self.assertTrue(self.group.refresh_called)
        self.assertIn(self.instance.name, str(SoftwareTimer.timer.schedule))

        # Simulate interrupt triggered by falling pin
        self.instance.sensor.pin_state = 0
        self.instance.pin_interrupt()
        asyncio.run(asyncio.sleep_ms(10))

        # Confirm nothing changed (targets stay on until reset timer expires)
        self.assertTrue(self.instance.motion)
        self.assertIn(self.instance.name, str(SoftwareTimer.timer.schedule))
        self.assertTrue(self.group.refresh_called)

    @cpython_only
    def test_12_pin_interrupt_no_reset_timer(self):
        # Set rule to 0 (disable reset timer)
        self.instance.current_rule = 0
        # Set motion False, targets off, stop reset timer
        self.instance.motion = False
        self.group.refresh_called = False
        SoftwareTimer.timer.cancel(self.instance.name)
        # Yield to let SoftwareTimer coroutine cancel reset timer
        asyncio.run(asyncio.sleep_ms(10))

        # Simulate interrupt triggered by rising pin
        self.instance.sensor.pin_state = 1
        self.instance.pin_interrupt()
        # Yield to let SoftwareTimer coroutine create reset timer
        asyncio.run(asyncio.sleep_ms(10))

        # Confirm motion detected, targets turned on, reset timer NOT running
        self.assertTrue(self.instance.motion)
        self.assertTrue(self.group.refresh_called)
        self.assertTrue(self.instance.name not in str(SoftwareTimer.timer.schedule))

        # Simulate interrupt triggered by falling pin
        self.group.refresh_called = False
        self.instance.sensor.pin_state = 0
        self.instance.pin_interrupt()
        asyncio.run(asyncio.sleep_ms(10))

        # Confirm motion not detected, targets turned off
        self.assertFalse(self.instance.motion)
        self.assertTrue(self.group.refresh_called)

    @cpython_only
    def test_13_reset_timer_motion_still_detected(self):
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
        # Yield to let SoftwareTimer coroutine create reset timer
        asyncio.run(asyncio.sleep_ms(10))

        # Confirm reset timer was restarted when old timer expired (prevent
        # getting stuck ON if timer expires before motion stops)
        self.assertIn(self.instance.name, str(SoftwareTimer.timer.schedule))

        # Confirm motion is still True
        self.assertTrue(self.instance.motion)

    # Original bug: Some sensors crashed or behaved unexpectedly if default_rule
    # was "enabled" or "disabled". Init method now raises exception to prevent
    # this, should not be possible to instantiate with invalid default_rule.
    def test_14_regression_invalid_default_rule(self):
        with self.assertRaises(AttributeError):
            MotionSensor("sensor1", "sensor1", "pir", "disabled", [], 15)

        with self.assertRaises(AttributeError):
            MotionSensor("sensor1", "sensor1", "ld2410", "enabled", [], 15)

    # Original bug: increment_rule cast argument to float and relied on try/except
    # to detect invalid argument. Since NaN is a valid float no exception was
    # raised and rule changed to NaN, leading to exception when motion detected.
    def test_15_regression_increment_by_nan(self):
        # Starting condition
        self.instance.set_rule(5)

        # Attempt to increment by NaN, confirm error, confirm rule does not change
        response = self.instance.increment_rule("NaN")
        self.assertEqual(response, {'ERROR': 'Invalid argument nan'})
        self.assertEqual(self.instance.current_rule, 5.0)

    # Original bug: validator accepted any argument that could be cast to float.
    # Since NaN is a valid float it was accepted, leading to a broken reset timer.
    def test_16_regression_validator_accepts_nan(self):
        # Attempt to set rule to NaN, should reject
        self.assertFalse(self.instance.set_rule("NaN"))

    # Original bug: Reset timer started when motion detected or schedule rule
    # changed, but not when set_rule endpoint was called. If the existing timer
    # was going to expire in 30 seconds when rule was changed to 10 minutes it
    # would incorrectly expire early. Now restarts timer after applying new rule.
    def test_17_regression_rule_change_does_not_start_timer(self):
        # Simulate motion detected, confirm timer started
        self.instance.motion_detected()
        # Yield to let SoftwareTimer coroutine create reset timer
        asyncio.run(asyncio.sleep_ms(10))
        self.assertIn(self.instance.name, str(SoftwareTimer.timer.schedule))

        # Manually cancel timer, confirm not running
        SoftwareTimer.timer.cancel(self.instance.name)
        asyncio.run(asyncio.sleep_ms(10))
        self.assertTrue(self.instance.name not in str(SoftwareTimer.timer.schedule))

        # Change rule, confirm timer recreated
        self.instance.set_rule(5)
        # Yield to let SoftwareTimer coroutine create reset timer
        asyncio.run(asyncio.sleep_ms(10))
        self.assertIn(self.instance.name, str(SoftwareTimer.timer.schedule))
