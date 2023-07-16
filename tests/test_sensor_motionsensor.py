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
            "test_reset_timer",
            "test_trigger",
            "test_enable_after_disable_by_rule_change",
            "test_regression_invalid_default_rule"
        ]

    @classmethod
    def setUpClass(cls):
        cls.instance = MotionSensor("sensor1", "sensor1", "pir", None, [], 15)

    def test_initial_state(self):
        self.assertIsInstance(self.instance, MotionSensor)
        self.assertTrue(self.instance.enabled)
        self.assertFalse(self.instance.motion)
        self.assertEqual(self.instance.sensor.value(), 0)

    def test_get_attributes(self):
        attributes = self.instance.get_attributes()
        self.assertEqual(attributes, expected_attributes)

    def test_rule_validation_valid(self):
        self.assertEqual(self.instance.rule_validator(5), 5.0)
        self.assertEqual(self.instance.rule_validator(0.5), 0.5)
        self.assertEqual(self.instance.rule_validator("0.5"), 0.5)
        self.assertEqual(self.instance.rule_validator("Disabled"), "disabled")
        self.assertEqual(self.instance.rule_validator(None), 0.0)

    def test_rule_validation_invalid(self):
        self.assertFalse(self.instance.rule_validator(True))
        self.assertFalse(self.instance.rule_validator("string"))
        self.assertFalse(self.instance.rule_validator([10]))
        self.assertFalse(self.instance.rule_validator({5: 5}))
        self.assertFalse(self.instance.rule_validator("None"))

    def test_rule_change(self):
        self.assertTrue(self.instance.set_rule(5))
        self.assertEqual(self.instance.current_rule, 5)
        self.assertTrue(self.instance.set_rule("1.5"))
        self.assertEqual(self.instance.current_rule, 1.5)

    def test_enable_disable(self):
        self.instance.disable()
        self.assertFalse(self.instance.enabled)
        self.instance.enable()
        self.assertTrue(self.instance.enabled)

    def test_disable_by_rule_change(self):
        self.instance.set_rule("Disabled")
        self.assertFalse(self.instance.enabled)

    def test_enable_by_rule_change(self):
        self.instance.set_rule(1)
        self.assertTrue(self.instance.enabled)

    def test_reset_timer(self):
        # Make sure rule isn't None (no timer set)
        self.instance.set_rule(1)
        # Call method triggered by hware interrupt
        self.instance.motion_detected()
        # SoftwareTimer queue should now contain entry containing sensor's name attribute
        self.assertIn(self.instance.name, str(SoftwareTimer.timer.schedule))
        # Motion attribute should be True
        self.assertTrue(self.instance.motion)

    def test_trigger(self):
        # Ensure not already tiggered to avoid false positive
        self.instance.motion = False
        # Trigger, condition should now be met
        self.assertTrue(self.instance.trigger())
        self.assertTrue(self.instance.condition_met())

    def test_enable_after_disable_by_rule_change(self):
        # Disable by rule change, enable with method
        self.instance.set_rule("disabled")
        self.instance.enable()
        # Old rule ("disabled") should have been automatically replaced by scheduled_rule
        self.assertEqual(self.instance.current_rule, self.instance.scheduled_rule)

    # Original bug: Some sensors would crash or behave unexpectedly if default_rule was "enabled" or "disabled"
    # in various situations. These classes now raise exception in init method to prevent this.
    # It should no longer be possible to instantiate with invalid default_rule.
    def test_regression_invalid_default_rule(self):
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
