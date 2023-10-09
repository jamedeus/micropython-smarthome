import sys
import json
import network
import unittest
from Api import app
from ApiTarget import ApiTarget
from MotionSensor import MotionSensor
from cpython_only import cpython_only

# Import dependencies for tests that only run in mocked environment
if sys.implementation.name == 'cpython':
    from unittest.mock import patch

# Read mock API receiver address
with open('config.json', 'r') as file:
    config = json.load(file)

# Connect to network if not connected (get node_ip for expected_attributes)
wlan = network.WLAN(network.STA_IF)
if not wlan.isconnected():
    wlan.connect(config['wifi']['ssid'], config['wifi']['password'])
    while not wlan.isconnected():
        continue

default_rule = {'on': ['enable', 'device1'], 'off': ['enable', 'device1']}

# Expected return value of get_attributes method just after instantiation
expected_attributes = {
    'triggered_by': ['sensor1'],
    'nickname': 'device1',
    'ip': config['mock_receiver']['ip'],
    'port': config['mock_receiver']['api_port'],
    'node_ip': wlan.ifconfig()[0],
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


# Mock Config class used in self-target tests
class MockConfig():
    def __init__(self, target):
        self.target = target

    def find(self, target):
        if target == 'device1':
            return self.target
        else:
            return False


# Mock Device class used in self-target tests
class MockDevice():
    def __init__(self):
        self.name = 'device1'
        self.enabled = True

    def enable(self):
        self.enabled = True

    def disable(self):
        self.enabled = False


class TestApiTarget(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Ensure wifi connected before instantiating (set correct node_ip)
        # Required for cpython test environment (loads all tests before running
        # any, possible for other test to disconnect wifi before reaching this)
        if not wlan.isconnected():
            wlan.connect(config['wifi']['ssid'], config['wifi']['password'])
            while not wlan.isconnected():
                continue

        # Create test instance with IP and port from config file
        ip = config["mock_receiver"]["ip"]
        port = config['mock_receiver']['api_port']
        cls.instance = ApiTarget("device1", "device1", "api-target", default_rule, ip, port)

        # Add mock MotionSensor triggering test instance
        cls.instance.triggered_by = [MotionSensor('sensor1', 'sensor1', 'pir', '5', [], 4)]

        # Create mock device and config for self-target tests
        cls.target = MockDevice()
        cls.config = MockConfig(cls.target)

    def tearDown(self):
        # Revert IP (prevent other tests failing if self-target fails)
        self.instance.ip = config["mock_receiver"]["ip"]

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

    # Different send method used when targeting own IP
    def test_13_send_to_self(self):
        # Set target IP to own IP
        self.instance.ip = wlan.ifconfig()[0]

        # Pass mock Config to API, set rule to enable and disable mock device
        app.config = self.config
        self.assertTrue(self.instance.set_rule({'on': ['enable', 'device1'], 'off': ['disable', 'device1']}))

        # Turn off, confirm mock device disabled
        self.assertTrue(self.instance.send(0))
        self.assertFalse(self.target.enabled)

        # Turn on, confirm mock device enabled
        self.assertTrue(self.instance.send(1))
        self.assertTrue(self.target.enabled)

        # Switch to invalid target, confirm both fail
        self.instance.set_rule({'on': ['enable', 'device2'], 'off': ['disable', 'device2']})
        self.assertFalse(self.instance.send(0))
        self.assertFalse(self.instance.send(1))

        # Revert IP
        self.instance.ip = config["mock_receiver"]["ip"]

    # Original bug: ApiTarget class overwrites parent set_rule method and did not include conditional
    # that overwrites "enabled" with default_rule. This resulted in an unusable rule which caused
    # crash next time send method was called.
    def test_14_regression_rule_change_to_enabled(self):
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
    def test_15_regression_invalid_default_rule(self):
        with self.assertRaises(AttributeError):
            ApiTarget("device1", "device1", "api-target", "disabled", config["mock_receiver"]["ip"])

        with self.assertRaises(AttributeError):
            ApiTarget("device1", "device1", "api-target", "enabled", config["mock_receiver"]["ip"])

    # Original bug: Rejected turn_on, turn_off, reset_rule commands (all valid)
    def test_16_regression_rejects_valid_rules(self):
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

    # Original bug: A typo in 187eb8d2 caused the send method to use the "on" rule
    # regardless of state argument. This was not detected for 2 weeks because no
    # existing tests verified that on and off rules were used correctly.
    @cpython_only
    def test_17_regression_send_ignores_state(self):
        # Set different on and off rules
        self.instance.set_rule({'on': ['turn_on', 'device2'], 'off': ['turn_off', 'device2']})

        # Call send with mocked request method to
        with patch.object(ApiTarget, 'request', return_value=True) as mock_request:
            # Turn on, confirm correct arg passed
            self.instance.send(1)
            self.assertEqual(mock_request.call_args_list[0][0][0], ['turn_on', 'device2'])

            # Turn off, confirm correct arg passed
            self.instance.send(0)
            self.assertEqual(mock_request.call_args_list[1][0][0], ['turn_off', 'device2'])

    # Original bug: When disabled send(1) was ignored, but send(0) was not (this is
    # intentional to prevent targets getting stuck if user manually turns on). When
    # current_rule was "disabled" this resulted in an uncaught exception when trying
    # to access sub-rule (using string key as index in a string). Fixed by returning
    # True immediately if rule is not dict.
    def test_18_regression_turn_off_while_rule_is_disabled(self):
        # Disable by setting rule to "Disabled"
        self.instance.set_rule("Disabled")
        self.assertFalse(self.instance.enabled)

        # Send method should return True immediately without doing anything
        self.assertTrue(self.instance.send(1))
        self.assertTrue(self.instance.send(0))
