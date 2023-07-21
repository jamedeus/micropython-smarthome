import time
import unittest
import SoftwareTimer
from DimmableLight import DimmableLight


class TestDimmableLight(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Instantiate with default_rule 50, min_bright 1, max_bright 100
        cls.instance = DimmableLight("device1", "device1", "DimmableLight", True, 50, 50, "1", "100")

        # Detect if mock send method was called
        cls.instance.send_method_called = False

        # Mock send method
        def send(arg=None):
            cls.instance.send_method_called = True
            return True
        cls.instance.send = send

    def test_01_initial_state(self):
        # Confirm min/max cast to int
        self.assertIsInstance(self.instance, DimmableLight)
        self.assertIsInstance(self.instance.min_bright, int)
        self.assertIsInstance(self.instance.max_bright, int)
        self.assertFalse(self.instance.fading)

    def test_02_instantiate_with_invalid_min_max(self):
        # AttributeError should be raised if default_rule is outside limits
        try:
            DimmableLight("device1", "device1", "DimmableLight", True, 50, 500, "1", "100")
            # Should not make it to this line, test failed
            self.assertFalse(True)
        except AttributeError:
            # Should raise exception, test passed
            self.assertTrue(True)

    def test_03_increment_invalid_rule(self):
        # Set non-integer rule
        self.instance.current_rule = 'disabled'
        # Attempt to increment, confirm error
        self.assertEqual(
            self.instance.increment_rule(1),
            {"ERROR": "Unable to increment current rule (disabled)"}
        )

    def test_04_increment_rule_out_of_range(self):
        # Set rule to max_bright
        self.instance.set_rule(100)
        # Increment should still return True
        self.assertTrue(self.instance.increment_rule(1))
        # Confirm rule did not change
        self.assertEqual(self.instance.current_rule, 100)

        # Repeat for min_bright
        self.instance.set_rule(1)
        self.assertTrue(self.instance.increment_rule(-1))
        self.assertEqual(self.instance.current_rule, 1)

    def test_05_set_invalid_rule(self):
        # Attempt to set rule exceeding max_bright, should return False
        self.assertFalse(self.instance.set_rule(999))

    def test_06_set_rule_while_state_is_true(self):
        # Change rule while device turned on, confirm send method called
        self.instance.state = True
        self.assertFalse(self.instance.send_method_called)
        self.assertTrue(self.instance.set_rule(50))
        self.assertTrue(self.instance.send_method_called)
        self.instance.send_method_called = False

    def test_07_fade_rule_on_boot(self):
        # Set rule to None, simulate first rule on boot
        self.instance.current_rule = None
        # Set fade rule, should immediately set current_rule to target
        self.assertTrue(self.instance.set_rule('fade/100/3600'))
        self.assertEqual(self.instance.current_rule, 100)
        # Confirm not fading, no timer created
        self.assertFalse(self.instance.fading)
        self.assertTrue(f'{self.instance.name}_fade' not in str(SoftwareTimer.timer.schedule))

    def test_08_start_fade_already_at_target(self):
        # Attempt to fade to current_rule, should return immediately
        self.instance.current_rule = 100
        self.assertTrue(self.instance.set_rule('fade/100/3600'))
        # Confirm not fading, no timer created
        self.assertFalse(self.instance.fading)
        self.assertTrue(f'{self.instance.name}_fade' not in str(SoftwareTimer.timer.schedule))

    def test_09_start_fade_while_disabled(self):
        # Attempt to fade to 100 while disabled
        self.instance.current_rule = 'disabled'
        self.assertTrue(self.instance.set_rule('fade/100/3600'))
        # Confirm timer created, starting brightness = 0
        self.assertEqual(self.instance.fading['starting_brightness'], 0)
        self.assertIn(f'{self.instance.name}_fade', str(SoftwareTimer.timer.schedule))
        SoftwareTimer.timer.cancel(f'{self.instance.name}_fade')

    def test_10_fade_complete(self):
        # Simulate fade up in progress
        self.instance.fading = {
            "started": SoftwareTimer.timer.epoch_now(),
            "starting_brightness": 1,
            "target": 50,
            "period": 1000,
            "down": False
        }
        # Simulate target rule reached
        self.instance.current_rule = 50
        self.assertTrue(self.instance.fade_complete())
        # Confirm fade dict removed
        self.assertFalse(self.instance.fading)

        # Simulate fade down in progress
        self.instance.fading = {
            "started": SoftwareTimer.timer.epoch_now(),
            "starting_brightness": 100,
            "target": 0,
            "period": 1000,
            "down": True
        }
        self.instance.state = True
        # Simulate target rule reached
        self.instance.current_rule = 0
        self.assertTrue(self.instance.fade_complete())
        # Confirm fade dict removed
        self.assertFalse(self.instance.fading)
        self.assertFalse(self.instance.state)

    def test_11_disable_while_fading(self):
        # Simulate fade in progress
        self.instance.fading = {
            "started": SoftwareTimer.timer.epoch_now(),
            "starting_brightness": 1,
            "target": 50,
            "period": 1000,
            "down": False
        }
        # Disable, confirm fade completes
        self.instance.enabled = False
        self.assertTrue(self.instance.fade_complete())
        self.assertFalse(self.instance.fading)
        self.instance.enable()

    def test_12_fade_method(self):
        # Simulate fading up to 50 in 1 second
        self.instance.set_rule(1)
        self.instance.fading = {
            "started": SoftwareTimer.timer.epoch_now(),
            "starting_brightness": 1,
            "target": 50,
            "period": 20,
            "down": False
        }
        # Wait for fade to complete, call method, confirm correct rule
        time.sleep_ms(1100)
        self.instance.fade()
        self.assertEqual(self.instance.current_rule, 50)
        self.assertFalse(self.instance.fading)

        # Simulate fading down to 1 in 1 seconnd
        self.instance.fading = {
            "started": SoftwareTimer.timer.epoch_now(),
            "starting_brightness": 50,
            "target": 1,
            "period": 20,
            "down": True
        }

        # Set state to True (send method should be called when new rule set)
        self.instance.state = True
        self.assertFalse(self.instance.send_method_called)

        # Wait for fade to complete, call method, confirm correct rule
        time.sleep_ms(1100)
        self.instance.fade()
        self.assertEqual(self.instance.current_rule, 1)
        self.assertFalse(self.instance.fading)
        # Confirm send method called
        self.assertTrue(self.instance.send_method_called)

        # Simulate fading up to 100 in 100 seconds
        self.instance.fading = {
            "started": SoftwareTimer.timer.epoch_now(),
            "starting_brightness": 1,
            "target": 100,
            "period": 1000,
            "down": False
        }

        # Confirm no fade timer in queue
        SoftwareTimer.timer.cancel(f'{self.instance.name}_fade')
        self.assertTrue(f'{self.instance.name}_fade' not in str(SoftwareTimer.timer.schedule))

        # Wait for 1 step, call method, confirm correct rule
        time.sleep_ms(1000)
        self.instance.fade()
        self.assertEqual(self.instance.current_rule, 2)
        self.assertTrue(self.instance.fading)

        # Confirm timer exists in queue
        self.assertIn(f'{self.instance.name}_fade', str(SoftwareTimer.timer.schedule))
