import json
import unittest
from ApiTarget import ApiTarget
from MotionSensor import MotionSensor

# Read mock API receiver address
with open('config.json', 'r') as file:
    config = json.load(file)

default_rule = {'on': ['enable', 'device1'], 'off': ['enable', 'device1']}

# Expected return value of get_attributes method just after instantiation
expected_attributes = {
    'triggered_by': ['sensor1'],
    'nickname': 'device1',
    'ip': config['mock_receiver']['ip'],
    'port': config['mock_receiver']['api_port'],
    'enabled': True,
    'rule_queue': [],
    'state': None,
    'default_rule': {
        'on': [
            'enable',
            'device1'
        ],
        'off': [
            'enable',
            'device1'
        ]
    },
    'name': 'device1',
    '_type': 'api-target',
    'scheduled_rule': None,
    'current_rule': None
}


class TestApiTarget(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Create test instance with IP and port from config file
        ip = config["mock_receiver"]["ip"]
        port = config['mock_receiver']['api_port']
        cls.instance = ApiTarget("device1", "device1", "api-target", default_rule, ip, port)

        # Add mock MotionSensor triggering test instance
        cls.instance.triggered_by = [MotionSensor('sensor1', 'sensor1', 'pir', '5', [], 4)]

    def test_01_initial_state(self):
        # Confirm expected attributes just after instantiation
        self.assertIsInstance(self.instance, ApiTarget)
        self.assertTrue(self.instance.enabled)
        self.assertEqual(self.instance.ip, config["mock_receiver"]["ip"])

    def test_02_get_attributes(self):
        # Confirm expected attributes dict just after instantiation
        attributes = self.instance.get_attributes()
        self.assertEqual(attributes, expected_attributes)

    def test_03_rule_validation_valid(self):
        # Should accept dict rules with correct keys and valid API commands
        self.assertEqual(
            self.instance.rule_validator({'on': ['trigger_sensor', 'sensor1'], 'off': ['enable', 'sensor1']}),
            {'on': ['trigger_sensor', 'sensor1'], 'off': ['enable', 'sensor1']}
        )
        self.assertEqual(
            self.instance.rule_validator({'on': ['enable_in', 'sensor1', 5], 'off': ['ignore']}),
            {'on': ['enable_in', 'sensor1', 5], 'off': ['ignore']}
        )
        self.assertEqual(
            self.instance.rule_validator({'on': ['set_rule', 'sensor1', 5], 'off': ['ignore']}),
            {'on': ['set_rule', 'sensor1', 5], 'off': ['ignore']}
        )
        self.assertEqual(
            self.instance.rule_validator({'on': ['ir_key', 'ac', 'start'], 'off': ['ignore']}),
            {'on': ['ir_key', 'ac', 'start'], 'off': ['ignore']}
        )

        # Should accept enabled and disabled, case-insensitive
        self.assertEqual(self.instance.rule_validator("Disabled"), "disabled")
        self.assertEqual(self.instance.rule_validator("disabled"), "disabled")

    def test_04_rule_validation_invalid(self):
        # Should reject rules with invalid API calls (missing args, incompatible args, etc)
        self.assertFalse(self.instance.rule_validator({'on': ['trigger_sensor', 'device1'], 'off': ['ignore']}))
        self.assertFalse(self.instance.rule_validator({'on': ['enable_in', 'sensor1', "string"], 'off': ['ignore']}))
        self.assertFalse(self.instance.rule_validator({'on': ['set_rule'], 'off': ['ignore']}))
        self.assertFalse(self.instance.rule_validator({'on': ['ir_key'], 'off': ['enable', 'sensor1']}))

        # Should reject invalid keys (case-sensitive)
        self.assertFalse(self.instance.rule_validator({'ON': ['set_rule', 'sensor1', 5], 'OFF': ['ignore']}))

        # Should reject too few keys
        self.assertFalse(self.instance.rule_validator({'Disabled': 'disabled'}))

        # Should reject non-dict
        self.assertFalse(self.instance.rule_validator(100))
        self.assertFalse(self.instance.rule_validator('string'))

        # Should reject dict with correct keys if values are not lists
        self.assertFalse(self.instance.rule_validator({'on': 100, 'off': 0}))

    def test_05_rule_change(self):
        # Should accept valid rule, confirm rule changed
        self.assertTrue(self.instance.set_rule({'on': ['set_rule', 'sensor1', 5], 'off': ['ignore']}))
        self.assertEqual(self.instance.current_rule, {'on': ['set_rule', 'sensor1', 5], 'off': ['ignore']})

        # Should accept string representation of dict, cast to dict automatically
        self.assertTrue(self.instance.set_rule('{"on":["ir_key","tv","power"],"off":["ir_key","tv","power"]}'))
        self.assertEqual(
            self.instance.current_rule,
            {"on": ["ir_key", "tv", "power"], "off": ["ir_key", "tv", "power"]}
        )

        # Should accept rule with both API call and ignore
        self.assertTrue(self.instance.set_rule({'on': ['ir_key', 'ac', 'start'], 'off': ['ignore']}))
        self.assertEqual(self.instance.current_rule, {'on': ['ir_key', 'ac', 'start'], 'off': ['ignore']})

        # Should reject invalid rule
        self.assertFalse(self.instance.set_rule('100'))
        self.assertEqual(self.instance.current_rule, {'on': ['ir_key', 'ac', 'start'], 'off': ['ignore']})

    def test_06_enable_by_rule_change(self):
        # Set rule while disabled, confirm rule takes effect, confirm enabled automatically
        self.instance.disable()
        self.assertFalse(self.instance.enabled)
        self.instance.set_rule({'on': ['set_rule', 'sensor1', 5], 'off': ['ignore']})
        self.assertEqual(self.instance.current_rule, {'on': ['set_rule', 'sensor1', 5], 'off': ['ignore']})
        self.assertTrue(self.instance.enabled)

        # Set state to True, change rule, send should be called
        self.instance.state = True
        self.instance.set_rule({'on': ['ignore'], 'off': ['ignore']})
        self.instance.state = False

    def test_07_disable_by_rule_change(self):
        # Set rule to disabled, confirm rule changed, confirm disabled
        self.instance.enable()
        self.assertTrue(self.instance.enabled)
        self.instance.set_rule("disabled")
        self.assertEqual(self.instance.current_rule, "disabled")
        self.assertFalse(self.instance.enabled)

    def test_08_send_while_disabled(self):
        # Confirm disabled, send should return True without doing anything
        self.assertFalse(self.instance.enabled)
        self.assertTrue(self.instance.send(1))
        self.instance.enable()

    def test_09_send_while_rule_is_ignore(self):
        # Set rules to ignore, send should return True without doing anything
        self.instance.set_rule({'on': ['ignore'], 'off': ['ignore']})
        self.assertTrue(self.instance.send(0))
        self.assertTrue(self.instance.send(1))

    def test_10_send_with_invalid_rule(self):
        # Set invalid rules, send should return False
        self.instance.current_rule = {'on': ['invalid'], 'off': ['invalid']}
        self.assertFalse(self.instance.send(0))
        self.assertFalse(self.instance.send(1))

    def test_11_network_error_in_send(self):
        # Set arbitrary rule that causes mock receiver to close connection early
        self.instance.current_rule['on'] = ['raise_exception']
        # Confirm failure detected
        self.assertFalse(self.instance.send(1))

    # When targetted by MotionSensor, ApiTarget should reset motion attribute after
    # successful on command. This allows retriggering sensor to send command again
    def test_12_send_retrigger_motion_sensor(self):
        # Set mock sensor motion attribute to True, set valid rule
        self.instance.triggered_by[0].motion = True
        self.instance.current_rule = {'on': ['trigger_sensor', 'sensor1'], 'off': ['ignore']}
        # Send, confirm motion flips to False
        self.assertTrue(self.instance.send(1))
        self.assertFalse(self.instance.triggered_by[0].motion)

    # Original bug: ApiTarget class overwrites parent set_rule method and did not include conditional
    # that overwrites "enabled" with default_rule. This resulted in an unusable rule which caused
    # crash next time send method was called.
    def test_13_regression_rule_change_to_enabled(self):
        self.instance.disable()
        self.assertFalse(self.instance.enabled)
        self.instance.set_rule('enabled')
        # Rule should be set to default rule, NOT 'enabled'
        self.assertEqual(self.instance.current_rule, default_rule)
        self.assertTrue(self.instance.enabled)
        # Attempt to reproduce crash, should not crash
        self.assertTrue(self.instance.send(1))

    # Original bug: Devices that use current_rule in send() payload crashed if default_rule was "enabled" or "disabled"
    # and current_rule changed to "enabled" (string rule instead of int in payload). These classes now raise exception
    # in init method to prevent this. It should no longer be possible to instantiate with invalid default_rule.
    def test_14_regression_invalid_default_rule(self):
        with self.assertRaises(AttributeError):
            ApiTarget("device1", "device1", "api-target", "disabled", config["mock_receiver"]["ip"])

        with self.assertRaises(AttributeError):
            ApiTarget("device1", "device1", "api-target", "enabled", config["mock_receiver"]["ip"])

    # Original bug: Rejected turn_on, turn_off, reset_rule commands (all valid)
    def test_15_regression_rejects_valid_rules(self):
        # Should accept turn_on/turn_off targeting device
        self.assertTrue(self.instance.set_rule({'on': ['turn_on', 'device2'], 'off': ['turn_off', 'device2']}))
        self.assertEqual(self.instance.current_rule, {'on': ['turn_on', 'device2'], 'off': ['turn_off', 'device2']})

        # Should accept reset_rule targetting device or sensor
        self.assertTrue(self.instance.set_rule({'on': ['reset_rule', 'device2'], 'off': ['reset_rule', 'sensor2']}))
        self.assertEqual(
            self.instance.current_rule,
            {'on': ['reset_rule', 'device2'], 'off': ['reset_rule', 'sensor2']}
        )

        # Should reject turn_on/turn_off for sensors
        self.assertFalse(self.instance.rule_validator({'on': ['turn_on', 'sensor1'], 'off': ['turn_off', 'sensor2']}))
