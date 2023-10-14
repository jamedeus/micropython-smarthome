import time
import unittest
import SoftwareTimer
from DimmableLight import DimmableLight


class TestDimmableLight(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Instantiate with default_rule 50, min_rule 1, max_rule 100
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
        self.assertIsInstance(self.instance.min_rule, int)
        self.assertIsInstance(self.instance.max_rule, int)
        self.assertFalse(self.instance.fading)

    def test_02_instantiate_with_invalid_min_max(self):
        # AttributeError should be raised if default_rule is outside limits
        with self.assertRaises(AttributeError):
            DimmableLight("device1", "device1", "DimmableLight", True, 50, 500, "1", "100")

    def test_03_rule_validation_valid(self):
        # Should accept int between min_rule and max_rule
        self.assertEqual(self.instance.rule_validator(1), 1)
        self.assertEqual(self.instance.rule_validator(51), 51)
        self.assertEqual(self.instance.rule_validator(100), 100)
        self.assertEqual(self.instance.rule_validator("42"), 42)
        # Should accept enabled and disabled (case-insensitive)
        self.assertEqual(self.instance.rule_validator("Disabled"), "disabled")
        self.assertEqual(self.instance.rule_validator("enabled"), "enabled")
        # Should accept fade rules if target is between min_rule and max_rule
        self.assertEqual(self.instance.rule_validator("fade/100/120"), "fade/100/120")
        self.assertEqual(self.instance.rule_validator("fade/1/120000"), "fade/1/120000")

    def test_04_rule_validation_invalid(self):
        # Should reject non-int rules
        self.assertFalse(self.instance.rule_validator(True))
        self.assertFalse(self.instance.rule_validator(None))
        self.assertFalse(self.instance.rule_validator("string"))
        self.assertFalse(self.instance.rule_validator([51]))
        self.assertFalse(self.instance.rule_validator({51: 51}))
        # Should reject integers less than min_rule or greater than max_rule
        self.assertFalse(self.instance.rule_validator(0))
        self.assertFalse(self.instance.rule_validator(-42))
        self.assertFalse(self.instance.rule_validator("-42"))
        self.assertFalse(self.instance.rule_validator(1337))
        # Should reject fade rules with target less than min_rule or greater than max_rule
        self.assertFalse(self.instance.rule_validator(["fade", "50", "1200"]))
        self.assertFalse(self.instance.rule_validator("fade/2000/15"))
        self.assertFalse(self.instance.rule_validator("fade/-512/600"))
        self.assertFalse(self.instance.rule_validator("fade/512/-600"))
        self.assertFalse(self.instance.rule_validator("fade/None/None"))
        self.assertFalse(self.instance.rule_validator("fade/1023/None"))
        self.assertFalse(self.instance.rule_validator("fade/None/120"))

    def test_05_increment_invalid_rule(self):
        # Set non-integer rule
        self.instance.current_rule = 'disabled'
        # Attempt to increment, confirm error
        self.assertEqual(
            self.instance.increment_rule(1),
            {"ERROR": "Unable to increment current rule (disabled)"}
        )

    def test_06_increment_rule_out_of_range(self):
        # Set rule to max_rule
        self.instance.set_rule(100)
        # Increment should still return True
        self.assertTrue(self.instance.increment_rule(1))
        # Confirm rule did not change
        self.assertEqual(self.instance.current_rule, 100)

        # Repeat for min_rule
        self.instance.set_rule(1)
        self.assertTrue(self.instance.increment_rule(-1))
        self.assertEqual(self.instance.current_rule, 1)

    def test_07_set_invalid_rule(self):
        # Attempt to set rule exceeding max_rule, should return False
        self.assertFalse(self.instance.set_rule(999))

    def test_08_set_rule_while_state_is_true(self):
        # Change rule while device turned on, confirm send method called
        self.instance.state = True
        self.assertFalse(self.instance.send_method_called)
        self.assertTrue(self.instance.set_rule(50))
        self.assertTrue(self.instance.send_method_called)
        self.instance.send_method_called = False

    def test_09_rule_change_while_fading(self):
        # Set starting brightness
        self.instance.set_rule(50)
        self.assertEqual(self.instance.current_rule, 50)

        # Start fading DOWN, confirm started, skip a few steps, confirm still fading
        self.instance.set_rule('fade/30/1800')
        self.assertTrue(self.instance.fading)
        self.instance.set_rule(40)
        self.assertEqual(self.instance.current_rule, 40)
        self.assertTrue(self.instance.fading)

        # Increase brightness - fade should abort despite being between start and target
        self.instance.set_rule(45)
        self.assertFalse(self.instance.fading)

        # Start fading UP, confirm started, skip a few steps, confirm still fading
        self.instance.set_rule('fade/90/1800')
        self.assertTrue(self.instance.fading)
        self.instance.set_rule(75)
        self.assertEqual(self.instance.current_rule, 75)
        self.assertTrue(self.instance.fading)

        # Decrease brightness - fade should abort despite being between start and target
        self.instance.set_rule(70)
        self.assertFalse(self.instance.fading)
        SoftwareTimer.timer.cancel(f'{self.instance.name}_fade')

    def test_10_fade_rule_on_boot(self):
        # Set rule to None, simulate first rule on boot
        self.instance.current_rule = None
        # Set fade rule, should immediately set current_rule to target
        self.assertTrue(self.instance.set_rule('fade/100/3600'))
        self.assertEqual(self.instance.current_rule, 100)
        # Confirm not fading, no timer created
        self.assertFalse(self.instance.fading)
        self.assertTrue(f'{self.instance.name}_fade' not in str(SoftwareTimer.timer.schedule))

    def test_11_start_fade_already_at_target(self):
        # Attempt to fade to current_rule, should return immediately
        self.instance.current_rule = 100
        self.assertTrue(self.instance.set_rule('fade/100/3600'))
        # Confirm not fading, no timer created
        self.assertFalse(self.instance.fading)
        self.assertTrue(f'{self.instance.name}_fade' not in str(SoftwareTimer.timer.schedule))

    def test_12_start_fade_while_disabled(self):
        # Attempt to fade to 100 while disabled
        self.instance.current_rule = 'disabled'
        self.assertTrue(self.instance.set_rule('fade/100/3600'))
        # Confirm timer created, starting brightness = min_rule
        self.assertEqual(self.instance.fading['starting_brightness'], self.instance.min_rule)
        self.assertIn(f'{self.instance.name}_fade', str(SoftwareTimer.timer.schedule))
        SoftwareTimer.timer.cancel(f'{self.instance.name}_fade')

    def test_13_fade_complete(self):
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

    def test_14_disable_while_fading(self):
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

    def test_15_fade_method(self):
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
        self.instance.send_method_called = False
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

    # Original bug: Devices that use current_rule in send() payload crashed if default_rule was "enabled" or "disabled"
    # and current_rule changed to "enabled" (string rule instead of int in payload). These classes now raise exception
    # in init method to prevent this. It should no longer be possible to instantiate with invalid default_rule.
    def test_16_regression_invalid_default_rule(self):
        with self.assertRaises(AttributeError):
            DimmableLight("device1", "device1", "DimmableLight", True, 50, "disabled", "1", "100")

        with self.assertRaises(AttributeError):
            DimmableLight("device1", "device1", "DimmableLight", True, 50, "enabled", "1", "100")

    # Original issue: DimmableLight.set_rule contains a conditional to abort an in-progress fade if
    # brightness is changed in the opposite direction. This is determined by checking if the new rule
    # is greater/less than current_rule, with no type checking on the new rule. This resulted in a
    # traceback when rule changed to a string (enabled, disabled) while fading.
    # Should now skip conditional if new rule is non-integer.
    def test_17_regression_rule_change_to_disabled_while_fading(self):
        # Set starting brightness
        self.instance.set_rule(50)
        self.assertEqual(self.instance.current_rule, 50)

        # Start fading DOWN, confirm started
        self.instance.set_rule('fade/30/1800')
        self.assertTrue(self.instance.fading)

        # Change rule to disabled, confirm changed, confirm no longer fading
        self.instance.set_rule('disabled')
        self.assertEqual(self.instance.current_rule, 'disabled')
        self.assertFalse(self.instance.fading)

    # Original issue: DimmableLight.start_fade handled current_rule == "disabled" by setting starting
    # point to min_rule, but did not change current_rule. This resulted in fade_complete canceling
    # the fade when the first step ran due to non-integer current_rule. Now calls set_rule(min_rule).
    def test_18_regression_start_fade_while_rule_is_disabled(self):
        # Set current_rule to disabled
        self.instance.set_rule('disabled')

        # Start fade to max brightness in 10 minutes, confirm correct fade dict and current_rule
        self.instance.set_rule('fade/100/600')
        self.assertTrue(isinstance(self.instance.fading, dict))
        self.assertEqual(self.instance.fading['starting_brightness'], self.instance.min_rule)
        self.assertEqual(self.instance.current_rule, self.instance.min_rule)

        # Run first step of fade, confirm fade is not canceled
        self.instance.fade()
        self.assertTrue(isinstance(self.instance.fading, dict))

    # Original issue: set_rule cast both arg and current_rule to int inside try/except,
    # which was intended to detect string current_rule (disabled etc) and return an error.
    # Invalid arguments also raised exceptions here and returned the same error, indicating
    # a problem with current_rule when the actual issue was the arg to increment_rule. Now
    # casts in 2 separate try/except blocks and returns more helpful errors.
    def test_19_regression_increment_rule_by_non_integer(self):
        # Starting condition
        self.instance.set_rule(70)

        # Attempt to increment by NaN, confirm error, confirm rule does not change
        response = self.instance.increment_rule("NaN")
        self.assertEqual(response, {'ERROR': 'Invalid argument NaN'})
        self.assertEqual(self.instance.current_rule, 70.0)

        # Attempt to increment by list, confirm error, confirm rule does not change
        response = self.instance.increment_rule([5])
        self.assertEqual(response, {'ERROR': 'Invalid argument [5]'})
        self.assertEqual(self.instance.current_rule, 70.0)
