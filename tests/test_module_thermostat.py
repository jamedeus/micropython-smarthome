import unittest
from Thermostat import Thermostat



class TestThermostat(unittest.TestCase):

    def __dir__(self):
        return ["test_instantiation", "test_rule_validation_valid", "test_rule_validation_invalid", "test_rule_change", "test_enable_disable", "", "test_disable_by_rule_change", "test_enable_by_rule_change", "test_sensor", "test_condition_met"]

    def test_instantiation(self):
        self.instance = Thermostat("sensor1", "si7021", True, 74, 74, [])
        self.assertIsInstance(self.instance, Thermostat)
        self.assertTrue(self.instance.enabled)

    def test_rule_validation_valid(self):
        self.assertEqual(self.instance.rule_validator(65), 65)
        self.assertEqual(self.instance.rule_validator(80), 80)
        self.assertEqual(self.instance.rule_validator("72"), 72)
        self.assertEqual(self.instance.rule_validator("Disabled"), "Disabled")

    def test_rule_validation_invalid(self):
        self.assertFalse(self.instance.rule_validator(64))
        self.assertFalse(self.instance.rule_validator(81))
        self.assertFalse(self.instance.rule_validator([72]))
        self.assertFalse(self.instance.rule_validator({72:72}))
        self.assertFalse(self.instance.rule_validator(True))
        self.assertFalse(self.instance.rule_validator(None))
        self.assertFalse(self.instance.rule_validator("string"))

    def test_rule_change(self):
        self.assertTrue(self.instance.set_rule(75))
        self.assertEqual(self.instance.current_rule, 75)

    def test_enable_disable(self):
        self.instance.disable()
        self.assertFalse(self.instance.enabled)
        self.instance.enable()
        self.assertTrue(self.instance.enabled)

    def test_disable_by_rule_change(self):
        self.instance.set_rule("Disabled")
        self.assertFalse(self.instance.enabled)

    def test_enable_by_rule_change(self):
        self.instance.set_rule(70)
        self.assertTrue(self.instance.enabled)

    def test_sensor(self):
        self.assertIsInstance(self.instance.fahrenheit(), float)
        self.assertIsInstance(self.instance.temp_sensor.temperature, float)
        self.assertIsInstance(self.instance.temp_sensor.relative_humidity, float)

    def test_condition_met(self):
        current = self.instance.fahrenheit()

        self.instance.set_rule(current)
        self.assertEqual(self.instance.condition_met(), None)

        self.instance.set_rule(current-2)
        self.assertFalse(self.instance.condition_met())

        self.instance.set_rule(current+2)
        self.assertTrue(self.instance.condition_met())

    def test_trigger(self):
        # Should not be able to trigger this sensor type
        self.assertFalse(self.instance.trigger())
