import unittest
from MotionSensor import MotionSensor
import SoftwareTimer
import time



class TestMotionSensor(unittest.TestCase):

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
        self.assertEqual(self.instance.rule_validator("Disabled"), "Disabled")
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
