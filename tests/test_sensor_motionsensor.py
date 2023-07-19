import unittest
from MotionSensor import MotionSensor
import SoftwareTimer

# Expected return value of get_attributes method just after instantiation
expected_attributes = {
    'targets': [],
    'nickname': 'sensor1',
    'motion': False,
    'enabled': True,
    'rule_queue': [],
    'name': 'sensor1',
    'default_rule': None,
    '_type': 'pir',
    'current_rule': None,
    'scheduled_rule': None
}


class TestMotionSensor(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.instance = MotionSensor("sensor1", "sensor1", "pir", None, [], 15)

    def test_01_initial_state(self):
        self.assertIsInstance(self.instance, MotionSensor)
        self.assertTrue(self.instance.enabled)
        self.assertFalse(self.instance.motion)
        self.assertEqual(self.instance.sensor.value(), 0)

    def test_02_get_attributes(self):
        attributes = self.instance.get_attributes()
        self.assertEqual(attributes, expected_attributes)

    def test_03_rule_validation_valid(self):
        self.assertEqual(self.instance.rule_validator(5), 5.0)
        self.assertEqual(self.instance.rule_validator(0.5), 0.5)
        self.assertEqual(self.instance.rule_validator("0.5"), 0.5)
        self.assertEqual(self.instance.rule_validator("Disabled"), "disabled")
        self.assertEqual(self.instance.rule_validator(None), 0.0)

    def test_04_rule_validation_invalid(self):
        self.assertFalse(self.instance.rule_validator(True))
        self.assertFalse(self.instance.rule_validator("string"))
        self.assertFalse(self.instance.rule_validator([10]))
        self.assertFalse(self.instance.rule_validator({5: 5}))
        self.assertFalse(self.instance.rule_validator("None"))

    def test_05_rule_change(self):
        self.assertTrue(self.instance.set_rule(5))
        self.assertEqual(self.instance.current_rule, 5)
        self.assertTrue(self.instance.set_rule("1.5"))
        self.assertEqual(self.instance.current_rule, 1.5)

    def test_06_enable_disable(self):
        self.instance.disable()
        self.assertFalse(self.instance.enabled)
        self.instance.enable()
        self.assertTrue(self.instance.enabled)

    def test_07_disable_by_rule_change(self):
        self.instance.set_rule("Disabled")
        self.assertFalse(self.instance.enabled)

    def test_08_enable_by_rule_change(self):
        self.instance.set_rule(1)
        self.assertTrue(self.instance.enabled)

    def test_09_reset_timer(self):
        # Make sure rule isn't None (no timer set)
        self.instance.set_rule(1)
        # Call method triggered by hware interrupt
        self.instance.motion_detected()
        # SoftwareTimer queue should now contain entry containing sensor's name attribute
        self.assertIn(self.instance.name, str(SoftwareTimer.timer.schedule))
        # Motion attribute should be True
        self.assertTrue(self.instance.motion)
        # Simulate reset timer expiring, motion should now be False
        self.instance.resetTimer()
        self.assertFalse(self.instance.motion)

        # Set rule to None, cancel previous timer to avoid false positive
        self.instance.set_rule(None)
        SoftwareTimer.timer.cancel(self.instance.name)
        # Call method triggered by hware interrupt
        self.instance.motion_detected()
        # Queue should NOT contain entry for motion sensor
        self.assertNotIn(self.instance.name, str(SoftwareTimer.timer.schedule))

    def test_10_trigger(self):
        # Ensure not already tiggered to avoid false positive
        self.instance.motion = False
        # Trigger, condition should now be met
        self.assertTrue(self.instance.trigger())
        self.assertTrue(self.instance.condition_met())

    def test_11_enable_after_disable_by_rule_change(self):
        # Disable by rule change, enable with method
        self.instance.set_rule("disabled")
        self.instance.enable()
        # Old rule ("disabled") should have been automatically replaced by scheduled_rule
        self.assertEqual(self.instance.current_rule, self.instance.scheduled_rule)

    def test_12_increment_rule(self):
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

    def test_13_next_rule(self):
        # Ensure enabled, confirm no reset timer in queu, set motion to True
        self.instance.enable()
        self.assertNotIn(self.instance.name, str(SoftwareTimer.timer.schedule))
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
        self.assertNotIn(self.instance.name, str(SoftwareTimer.timer.schedule))

    # Original bug: Some sensors would crash or behave unexpectedly if default_rule was "enabled" or "disabled"
    # in various situations. These classes now raise exception in init method to prevent this.
    # It should no longer be possible to instantiate with invalid default_rule.
    def test_14_regression_invalid_default_rule(self):
        # assertRaises fails for some reason, this approach seems reliable
        try:
            MotionSensor("sensor1", "sensor1", "pir", "disabled", [], 15)
            # Should not make it to this line, test failed
            self.assertFalse(True)
        except AttributeError:
            # Should raise exception, test passed
            self.assertTrue(True)

        try:
            MotionSensor("sensor1", "sensor1", "pir", "enabled", [], 15)
            # Should not make it to this line, test failed
            self.assertFalse(True)
        except AttributeError:
            # Should raise exception, test passed
            self.assertTrue(True)
