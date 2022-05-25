import unittest
from Desktop_trigger import Desktop_trigger



class TestDesktopTrigger(unittest.TestCase):
    def test_instantiation(self):
        self.instance = Desktop_trigger("sensor1", "desktop", True, None, None, [], "192.168.1.216")
        self.assertIsInstance(self.instance, Desktop_trigger)
        self.assertTrue(self.instance.enabled)

    def test_rule_validation_valid(self):
        self.assertIs(self.instance.rule_validator("Enabled"), "Enabled")
        self.assertIs(self.instance.rule_validator("Disabled"), "Disabled")

    def test_rule_validation_invalid(self):
        self.assertFalse(self.instance.rule_validator(True))
        self.assertFalse(self.instance.rule_validator(None))
        self.assertFalse(self.instance.rule_validator("string"))
        self.assertFalse(self.instance.rule_validator(42))
        self.assertFalse(self.instance.rule_validator(["Enabled"]))
        self.assertFalse(self.instance.rule_validator({"Enabled":"Enabled"}))
        self.assertFalse(self.instance.rule_validator("ENABLED"))

    def test_rule_change(self):
        self.assertTrue(self.instance.set_rule("Enabled"))
        self.assertEqual(self.instance.current_rule, 'Enabled')
        self.assertTrue(self.instance.enabled)

        self.assertTrue(self.instance.set_rule("Disabled"))
        self.assertEqual(self.instance.current_rule, 'Disabled')
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
