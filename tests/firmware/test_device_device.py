import unittest
from Group import Group
from Device import Device
from Sensor import Sensor

# Expected return value of get_attributes method just after instantiation
expected_attributes = {
    'nickname': 'Test',
    '_type': 'device',
    'scheduled_rule': 50,
    'current_rule': 'enabled',
    'default_rule': 50,
    'enabled': True,
    'group': 'group1',
    'rule_queue': [10, 20],
    'state': None,
    'name': 'device1',
    'triggered_by': ['sensor1']
}


# Mock subclass with send method + attributes used for testing
class MockDevice(Device):
    def __init__(self, name, nickname, _type, enabled, current_rule, default_rule):
        super().__init__(name, nickname, _type, enabled, current_rule, default_rule)

        # Used to confirm that send method was called
        self.send_method_called = False

        # Arbitrarily sets send method return value
        # Used to simulate failed send call
        self.send_result = True

    # Accept int in addition to enabled, disabled
    def validator(self, rule):
        if isinstance(rule, bool):
            return False
        elif isinstance(rule, int):
            return rule
        return False

    # Mock send method, tracks when called
    def send(self, arg=None):
        self.send_method_called = True
        return self.send_result

    # Intercept get_attributes dict and remove testing attributes
    def get_attributes(self):
        attributes = super().get_attributes()
        del attributes['send_method_called']
        del attributes['send_result']
        return attributes


class TestDevice(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Instantiate test device with mock subclass, add rules to queue
        cls.instance = MockDevice("device1", "Test", "device", True, "enabled", 50)
        cls.instance.rule_queue = [10, 20]
        cls.instance.scheduled_rule = cls.instance.default_rule

        # Create mock sensor targeting device, add both to mock group
        cls.sensor = Sensor('sensor1', 'sensor1', 'sensor', True, 'enabled', 'enabled', [cls.instance])
        cls.group = Group("group1", [cls.sensor])
        cls.instance.triggered_by.append(cls.sensor)
        cls.instance.group = cls.group

    def test_01_initial_state(self):
        # Confirm expected attributes just after instantiation
        self.assertIsInstance(self.instance, MockDevice)
        self.assertEqual(self.instance.name, "device1")
        self.assertEqual(self.instance.nickname, "Test")
        self.assertTrue(self.instance.enabled)
        self.assertEqual(self.instance.state, None)
        self.assertEqual(self.instance.current_rule, "enabled")
        self.assertEqual(self.instance.scheduled_rule, 50)
        self.assertEqual(self.instance.default_rule, 50)
        self.assertEqual(self.instance.triggered_by, [self.sensor])

    def test_02_get_attributes(self):
        # Confirm get_attributes dict has expected values, class objects removed
        attributes = self.instance.get_attributes()
        self.assertEqual(attributes, expected_attributes)

    def test_03_enable(self):
        # Set rule to disabled, confirm disabled
        self.instance.set_rule('disabled')
        self.assertFalse(self.instance.enabled)

        # Enable, confirm rule changes to scheduled_rule
        self.instance.enable()
        self.assertTrue(self.instance.enabled)
        self.assertEqual(self.instance.current_rule, self.instance.scheduled_rule)

    def test_04_enable_with_invalid_schedule_rule(self):
        # Set both current and scheduled rules disabled
        self.instance.set_rule('disabled')
        self.instance.scheduled_rule = 'disabled'
        self.assertFalse(self.instance.enabled)

        # Enable, confirm rule falls back to default_rule
        self.instance.enable()
        self.assertTrue(self.instance.enabled)
        self.assertEqual(self.instance.current_rule, self.instance.default_rule)

    def test_05_enable_with_group_turned_on(self):
        # Disable, set group state to True (devices turned on)
        self.instance.disable()
        self.group.state = True
        self.assertFalse(self.instance.state)
        self.instance.send_method_called = False
        self.assertFalse(self.instance.send_method_called)

        # Enable, confirm send method called
        self.instance.enable()
        self.assertTrue(self.instance.enabled)
        self.assertTrue(self.instance.state)
        self.assertTrue(self.instance.send_method_called)
        self.instance.send_method_called = False

    def test_06_enable_with_group_turned_on_failed_send_call(self):
        # Repeat while simulating failed send call
        self.instance.send_result = False
        self.instance.disable()
        self.group.state = True
        self.assertFalse(self.instance.state)
        self.instance.send_method_called = False
        self.assertFalse(self.instance.send_method_called)

        # Enable, confirm send method called, confirm group state set to False
        self.instance.enable()
        self.assertTrue(self.instance.enabled)
        self.assertFalse(self.instance.state)
        self.assertTrue(self.instance.send_method_called)
        self.instance.send_method_called = False

    def test_07_disable(self):
        # Confirm enabled
        self.instance.enable()
        self.assertTrue(self.instance.enabled)

        # Disable, confirm disabled
        self.instance.disable()
        self.assertFalse(self.instance.enabled)

    def test_08_disable_while_turned_on(self):
        # Starting conditions
        self.instance.enable()
        self.instance.state = True
        self.assertTrue(self.instance.enabled)
        self.instance.send_method_called = False

        # Disable, confirm disabled, confirm send called, confirm state False
        self.instance.disable()
        self.assertTrue(self.instance.send_method_called)
        self.assertFalse(self.instance.enabled)
        self.assertFalse(self.instance.state)

    def test_09_rule_validation_valid(self):
        # Should accept enabled, disabled, and int
        self.assertEqual(self.instance.rule_validator("Disabled"), "disabled")
        self.assertEqual(self.instance.rule_validator("enabled"), "enabled")
        self.assertEqual(self.instance.rule_validator(51), 51)
        self.assertEqual(self.instance.rule_validator(251), 251)

    def test_10_rule_validation_invalid(self):
        # Should reject all other rules
        self.assertFalse(self.instance.rule_validator(True))
        self.assertFalse(self.instance.rule_validator(False))
        self.assertFalse(self.instance.rule_validator(None))
        self.assertFalse(self.instance.rule_validator("string"))
        self.assertFalse(self.instance.rule_validator([51]))
        self.assertFalse(self.instance.rule_validator({51: 51}))
        self.assertFalse(self.instance.rule_validator("fade/123/120"))

    def test_11_set_rule(self):
        # Set rule, confirm rule changed
        self.instance.current_rule = 10
        self.assertTrue(self.instance.set_rule(50))
        self.assertEqual(self.instance.current_rule, 50)

        # Confirm rejects invalid rule
        self.assertFalse(self.instance.set_rule('string'))
        self.assertEqual(self.instance.current_rule, 50)

    def test_12_disable_by_rule_change(self):
        # Starting conditions
        self.assertTrue(self.instance.enabled)
        self.instance.send_method_called = False

        # Set rule to disabled, confirm disabled, confirm send method called
        self.instance.set_rule("Disabled")
        self.assertFalse(self.instance.enabled)
        self.assertTrue(self.instance.send_method_called)

    def test_13_enable_by_rule_change(self):
        # Starting conditions
        self.assertFalse(self.instance.enabled)
        self.instance.scheduled_rule = 50

        # Set rule to enabled, confirm rule falls back to scheduled_rule
        self.instance.set_rule("Enabled")
        self.assertTrue(self.instance.enabled)
        self.assertEqual(self.instance.current_rule, 50)

    def test_14_set_rule_while_disabled(self):
        # Confirm disabled
        self.instance.disable()
        self.assertFalse(self.instance.enabled)

        # Set rule, confirm enabled
        self.assertTrue(self.instance.set_rule(50))
        self.assertTrue(self.instance.enabled)

    def test_15_set_rule_while_turned_on(self):
        # Starting conditions
        self.instance.send_method_called = False
        self.instance.state = True

        # Set rule, confirm send method called
        self.assertTrue(self.instance.set_rule(100))
        self.assertTrue(self.instance.send_method_called)

    def test_16_next_rule(self):
        # Confirm current_rule doesn't match expected new rule
        self.assertNotEqual(self.instance.current_rule, 10)

        # Move to next rule, confirm correct rule
        self.instance.next_rule()
        self.assertEqual(self.instance.current_rule, 10)

    # Original bug: If set_rule was called with "enabled" the apply_new_rule
    # method would set current_rule to default_rule instead of scheduled_rule.
    def test_17_regression_enable_with_rule_change_ignores_scheduled_rule(self):
        # Starting conditions
        self.instance.disable()
        self.instance.scheduled_rule = 25
        self.instance.default_rule = 50
        self.assertFalse(self.instance.enabled)

        # Enable device by calling set_rule method
        self.assertTrue(self.instance.set_rule("enabled"))

        # Confirm switched to scheduled_rule, not default_rule
        self.assertEqual(self.instance.current_rule, 25)
