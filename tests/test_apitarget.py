import unittest
from ApiTarget import ApiTarget



class TestApiTarget(unittest.TestCase):

    def test_instantiation(self):
        self.instance = ApiTarget("device1", "api-target", True, None, None, "192.168.1.223")
        self.assertIsInstance(self.instance, ApiTarget)

    def test_initial_state(self):
        self.assertTrue(self.instance.enabled)

    def test_rule_validation_valid(self):
        self.assertEqual(self.instance.rule_validator({'on': ['trigger_sensor', 'sensor1'], 'off': ['enable', 'sensor1']}), {'on': ['trigger_sensor', 'sensor1'], 'off': ['enable', 'sensor1']})
        self.assertEqual(self.instance.rule_validator({'on': ['enable_in', 'sensor1', 5], 'off': ['ignore']}), {'on': ['enable_in', 'sensor1', 5], 'off': ['ignore']})
        self.assertEqual(self.instance.rule_validator({'on': ['set_rule', 'sensor1', 5], 'off': ['ignore']}), {'on': ['set_rule', 'sensor1', 5], 'off': ['ignore']})

    def test_rule_validation_invalid(self):
        self.assertFalse(self.instance.rule_validator({'on': ['trigger_sensor', 'device1'], 'off': ['enable', 'sensor1']}))
        self.assertFalse(self.instance.rule_validator({'on': ['enable_in', 'sensor1', "string"], 'off': ['ignore']}))
        self.assertFalse(self.instance.rule_validator({'on': ['set_rule'], 'off': ['ignore']}))
        self.assertFalse(self.instance.rule_validator({'ON': ['set_rule', 'sensor1', 5], 'OFF': ['ignore']}))

    def test_rule_change(self):
        self.assertTrue(self.instance.set_rule({'on': ['set_rule', 'sensor1', 5], 'off': ['ignore']}))
        self.assertEqual(self.instance.current_rule, {'on': ['set_rule', 'sensor1', 5], 'off': ['ignore']})

    def test_disable(self):
        self.instance.disable()
        self.assertFalse(self.instance.enabled)

    def test_enable(self):
        self.instance.enable()
        self.assertTrue(self.instance.enabled)

    def test_enable_by_rule_change(self):
        self.instance.disable()
        self.assertFalse(self.instance.enabled)
        self.instance.set_rule({'on': ['set_rule', 'sensor1', 5], 'off': ['ignore']})
        self.assertTrue(self.instance.enabled)
