import unittest
from MotionSensor import MotionSensor
import SoftwareTimer



class TestMotionSensor(unittest.TestCase):

    def __dir__(self):
        return ["test_instantiation", "test_rule_validation_valid", "test_rule_validation_invalid", "test_rule_change", "test_enable_disable", "test_disable_by_rule_change", "test_enable_by_rule_change", "test_reset_timer", "test_trigger", "test_enable_after_disable_by_rule_change"]

    def test_instantiation(self):
        self.instance = MotionSensor("sensor1", "pir", True, None, None, [], 15)
        self.assertIsInstance(self.instance, MotionSensor)
        self.assertTrue(self.instance.enabled)
        self.assertFalse(self.instance.motion)
        self.assertEqual(self.instance.sensor.value(), 0)

    def test_rule_validation_valid(self):
        self.assertEqual(self.instance.rule_validator(5), 5.0)
        self.assertEqual(self.instance.rule_validator(0.5), 0.5)
        self.assertEqual(self.instance.rule_validator("0.5"), 0.5)
        self.assertEqual(self.instance.rule_validator("Disabled"), "disabled")
        self.assertEqual(self.instance.rule_validator(None), None)

    def test_rule_validation_invalid(self):
        self.assertFalse(self.instance.rule_validator(True))
        self.assertFalse(self.instance.rule_validator("string"))
        self.assertFalse(self.instance.rule_validator([10]))
        self.assertFalse(self.instance.rule_validator({5:5}))
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
