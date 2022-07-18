import unittest
from Desktop_trigger import Desktop_trigger



class TestDesktopTrigger(unittest.TestCase):

    def __dir__(self):
        return ["test_instantiation", "test_rule_validation_valid", "test_rule_validation_invalid", "test_rule_change", "test_enable_disable", "test_get_idle_time", "test_get_monitor_state", "test_trigger"]

    def test_instantiation(self):
        self.instance = Desktop_trigger("sensor1", "desktop", True, None, None, [], "192.168.1.216")
        self.assertIsInstance(self.instance, Desktop_trigger)
        self.assertTrue(self.instance.enabled)

    def test_rule_validation_valid(self):
        self.assertIs(self.instance.rule_validator("enabled"), "enabled")
        self.assertIs(self.instance.rule_validator("Enabled"), "enabled")
        self.assertIs(self.instance.rule_validator("ENABLED"), "enabled")
        self.assertIs(self.instance.rule_validator("disabled"), "disabled")
        self.assertIs(self.instance.rule_validator("Disabled"), "disabled")

    def test_rule_validation_invalid(self):
        self.assertFalse(self.instance.rule_validator(True))
        self.assertFalse(self.instance.rule_validator(None))
        self.assertFalse(self.instance.rule_validator("string"))
        self.assertFalse(self.instance.rule_validator(42))
        self.assertFalse(self.instance.rule_validator(["Enabled"]))
        self.assertFalse(self.instance.rule_validator({"Enabled":"Enabled"}))

    def test_rule_change(self):
        self.assertTrue(self.instance.set_rule("Enabled"))
        self.assertEqual(self.instance.current_rule, 'enabled')
        self.assertTrue(self.instance.enabled)

        self.assertTrue(self.instance.set_rule("Disabled"))
        self.assertEqual(self.instance.current_rule, 'disabled')
        self.assertFalse(self.instance.enabled)

    def test_enable_disable(self):
        self.instance.disable()
        self.assertFalse(self.instance.enabled)
        self.instance.enable()
        self.assertTrue(self.instance.enabled)

    def test_get_idle_time(self):
        idle_time = self.instance.get_idle_time()
        self.assertIsInstance(idle_time, dict)
        self.assertIsInstance(int(idle_time["idle_time"]), int)

    def test_get_monitor_state(self):
        state = self.instance.get_monitor_state()
        self.assertIsInstance(state, str)
        self.assertIn(state, ['On', 'Off', 'Disabled'])

    def test_trigger(self):
        # Ensure not already triggered to avoid false positive
        self.instance.current = "Off"
        self.assertFalse(self.instance.condition_met())
        # Trigger, condition should now be met
        self.assertTrue(self.instance.trigger())
        self.assertTrue(self.instance.condition_met())
