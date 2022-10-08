import unittest
from ApiTarget import ApiTarget

default_rule = {'on': ['enable', 'device1'], 'off': ['enable', 'device1']}



class TestApiTarget(unittest.TestCase):

    def __dir__(self):
        return ["test_instantiation", "test_rule_validation_valid", "test_rule_validation_invalid", "test_rule_change", "test_enable_disable", "test_enable_by_rule_change", "test_disable_by_rule_change", "test_rule_change_to_enabled_regression", "test_regression_invalid_default_rule"]

    def test_instantiation(self):
        self.instance = ApiTarget("device1", "device1", "api-target", True, None, default_rule, "192.168.1.223")
        self.assertIsInstance(self.instance, ApiTarget)
        self.assertTrue(self.instance.enabled)

    def test_rule_validation_valid(self):
        self.assertEqual(self.instance.rule_validator({'on': ['trigger_sensor', 'sensor1'], 'off': ['enable', 'sensor1']}), {'on': ['trigger_sensor', 'sensor1'], 'off': ['enable', 'sensor1']})
        self.assertEqual(self.instance.rule_validator({'on': ['enable_in', 'sensor1', 5], 'off': ['ignore']}), {'on': ['enable_in', 'sensor1', 5], 'off': ['ignore']})
        self.assertEqual(self.instance.rule_validator({'on': ['set_rule', 'sensor1', 5], 'off': ['ignore']}), {'on': ['set_rule', 'sensor1', 5], 'off': ['ignore']})
        self.assertEqual(self.instance.rule_validator({'on': ['ir_key', 'ac', 'start'], 'off': ['ignore']}), {'on': ['ir_key', 'ac', 'start'], 'off': ['ignore']})
        self.assertEqual(self.instance.rule_validator("Disabled"), "disabled")
        self.assertEqual(self.instance.rule_validator("disabled"), "disabled")

    def test_rule_validation_invalid(self):
        self.assertFalse(self.instance.rule_validator({'on': ['trigger_sensor', 'device1'], 'off': ['enable', 'sensor1']}))
        self.assertFalse(self.instance.rule_validator({'on': ['enable_in', 'sensor1', "string"], 'off': ['ignore']}))
        self.assertFalse(self.instance.rule_validator({'on': ['set_rule'], 'off': ['ignore']}))
        self.assertFalse(self.instance.rule_validator({'ON': ['set_rule', 'sensor1', 5], 'OFF': ['ignore']}))
        self.assertFalse(self.instance.rule_validator({'Disabled':'disabled'}))

    def test_rule_change(self):
        self.assertTrue(self.instance.set_rule({'on': ['set_rule', 'sensor1', 5], 'off': ['ignore']}))
        self.assertEqual(self.instance.current_rule, {'on': ['set_rule', 'sensor1', 5], 'off': ['ignore']})
        # String rule should be converted to dict automatically
        self.assertTrue(self.instance.set_rule('{"on":["ir_key","tv","power"],"off":["ir_key","tv","power"]}'))
        self.assertEqual(self.instance.current_rule, {"on":["ir_key","tv","power"],"off":["ir_key","tv","power"]})
        # Should rule with both ir command and ignore
        self.assertTrue(self.instance.set_rule({'on': ['ir_key', 'ac', 'start'], 'off': ['ignore']}))
        self.assertEqual(self.instance.current_rule, {'on': ['ir_key', 'ac', 'start'], 'off': ['ignore']})

    def test_enable_disable(self):
        self.instance.disable()
        self.assertFalse(self.instance.enabled)
        self.instance.enable()
        self.assertTrue(self.instance.enabled)

    def test_enable_by_rule_change(self):
        self.instance.disable()
        self.assertFalse(self.instance.enabled)
        self.instance.set_rule({'on': ['set_rule', 'sensor1', 5], 'off': ['ignore']})
        self.assertTrue(self.instance.enabled)

    def test_disable_by_rule_change(self):
        self.instance.enable()
        self.assertTrue(self.instance.enabled)
        self.instance.set_rule("disabled")
        self.assertFalse(self.instance.enabled)

    # Original bug: ApiTarget class overwrites parent set_rule method and did not include conditional
    # that overwrites "enabled" with default_rule. This resulted in an unusable rule which caused
    # crash next time send method was called.
    def test_rule_change_to_enabled_regression(self):
        self.instance.disable()
        self.assertFalse(self.instance.enabled)
        self.instance.set_rule('enabled')
        # Rule should be set to default rule, NOT 'enabled'
        self.assertEqual(self.instance.current_rule, default_rule)
        self.assertTrue(self.instance.enabled)
        # Attempt to reproduce crash, should not crash
        self.assertTrue(self.instance.send(1))

    # Original bug: Device types that use current_rule in send() payload would crash if default_rule was "enabled" or "disabled"
    # and current_rule changed to "enabled" (string rule instead of int in payload). These classes now raise exception in init
    # method to prevent this. It should no longer be possible to instantiate with invalid default_rule.
    def test_regression_invalid_default_rule(self):
        # assertRaises fails for some reason, this approach seems reliable
        try:
            test = ApiTarget("device1", "device1", "api-target", True, None, "disabled", "192.168.1.223")
            # Should not make it to this line, test failed
            self.assertFalse(True)
        except AttributeError:
            # Should raise exception, test passed
            self.assertTrue(True)

        try:
            test = ApiTarget("device1", "device1", "api-target", True, None, "enabled", "192.168.1.223")
            # Should not make it to this line, test failed
            self.assertFalse(True)
        except AttributeError:
            # Should raise exception, test passed
            self.assertTrue(True)
