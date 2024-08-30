# pylint: disable=line-too-long, missing-function-docstring, missing-module-docstring, missing-class-docstring

from copy import deepcopy
from unittest import TestCase
from helper_functions import load_unit_test_config
from instance_validators import (
    validate_rules,
    api_target_validator,
    is_valid_ir_api_call,
    int_or_fade_validator,
    dummy_validator,
    int_or_float_validator,
    thermostat_validator
)


# Test functions in instance_validators.py not already covered by config generation tests
class ValidatorTests(TestCase):
    def setUp(self):
        # Load valid config
        self.config = load_unit_test_config()

    def test_api_target_single_param(self):
        # Should accept all 3 single-parameter commands
        valid = self.config['device9']['default_rule']
        valid['on'] = ['ignore']
        self.assertTrue(api_target_validator(valid))
        valid['on'] = ['reboot']
        self.assertTrue(api_target_validator(valid))
        valid['on'] = ['clear_log']
        self.assertTrue(api_target_validator(valid))

    def test_api_target_enable_disable(self):
        # Should accept accept enable and disable if arg is sensor or device
        valid = self.config['device9']['default_rule']
        valid['on'] = ['enable', 'sensor1']
        self.assertTrue(api_target_validator(valid))
        valid['on'] = ['disable', 'device1']
        self.assertTrue(api_target_validator(valid))

    def test_api_target_sensor_commands(self):
        # Should accept sensor-only commands if arg is sensor
        valid = self.config['device9']['default_rule']
        valid['on'] = ['trigger_sensor', 'sensor1']
        self.assertTrue(api_target_validator(valid))
        valid['on'] = ['condition_met', 'sensor1']
        self.assertTrue(api_target_validator(valid))
        # Should reject device
        valid['on'] = ['condition_met', 'device1']
        self.assertFalse(api_target_validator(valid))

    def test_api_target_enable_in_disable_in(self):
        # Should accept accept enable and disable if args ar sensor/device and int/float
        valid = self.config['device9']['default_rule']
        valid['on'] = ['enable_in', 'sensor1', '5']
        self.assertTrue(api_target_validator(valid))
        valid['on'] = ['disable_in', 'device1', '2.5']
        self.assertTrue(api_target_validator(valid))
        # Should fail with non-numeric delay
        valid['on'] = ['disable_in', 'device1', 'five minutes']
        self.assertFalse(api_target_validator(valid))

    def test_api_target_turn_on_turn_off(self):
        # Should accept turn_on/off if arg is device
        valid = self.config['device9']['default_rule']
        valid['on'] = ['turn_on', 'device1']
        self.assertTrue(api_target_validator(valid))
        valid['on'] = ['turn_off', 'device1']
        self.assertTrue(api_target_validator(valid))

    def test_api_target_set_rule(self):
        # Should accept set_rule if args are sensor/device and rule
        valid = self.config['device9']['default_rule']
        valid['on'] = ['set_rule', 'sensor1', '50']
        self.assertTrue(api_target_validator(valid))
        valid['on'] = ['set_rule', 'device1', '50']
        self.assertTrue(api_target_validator(valid))

        # Should accept reset_rule if arg is sensor or device
        valid['on'] = ['reset_rule', 'sensor1']
        self.assertTrue(api_target_validator(valid))
        valid['on'] = ['reset_rule', 'device1']
        self.assertTrue(api_target_validator(valid))

    def test_api_target_ir_key(self):
        # Should accept valid command
        valid = self.config['device9']['default_rule']
        self.assertTrue(api_target_validator(valid))
        # Should reject unknown args
        valid['on'] = ['ir_key', 'invalid', 'invalid', 'invalid']
        self.assertFalse(api_target_validator(valid))

    def test_fade_rules(self):
        # LedStrip, Tplink, and Wled should accept fade rules
        self.assertTrue(
            int_or_fade_validator('fade/50/3600', min_rule='0', max_rule='1023', _type='pwm')
        )
        self.assertTrue(
            int_or_fade_validator('fade/50/3600', min_rule='1', max_rule='100', _type='bulb')
        )
        self.assertTrue(int_or_fade_validator(
            'fade/50/3600', min_rule='1', max_rule='255', _type='wled')
        )

        # Should reject if target out of range
        self.assertFalse(
            int_or_fade_validator('fade/50/3600', min_rule='500', max_rule='1023', _type='pwm')
        )
        self.assertFalse(
            int_or_fade_validator('fade/50/3600', min_rule='75', max_rule='100', _type='bulb')
        )
        self.assertFalse(
            int_or_fade_validator('fade/50/3600', min_rule='128', max_rule='255', _type='wled')
        )

        # Should reject if target negative
        self.assertFalse(
            int_or_fade_validator('fade/-5/3600', min_rule='1', max_rule='100', _type='bulb')
        )
        self.assertEqual(
            int_or_fade_validator('fade/-5/3600', min_rule='-500', max_rule='1023', _type='pwm'),
            'Rule limits cannot be less than 0'
        )
        self.assertFalse(
            int_or_fade_validator('fade/-5/3600', min_rule='128', max_rule='255', _type='wled')
        )

        # Should reject if period negative
        self.assertFalse(
            int_or_fade_validator('fade/50/-500', min_rule='0', max_rule='1023', _type='pwm')
        )
        self.assertFalse(
            int_or_fade_validator('fade/50/-500', min_rule='1', max_rule='100', _type='bulb')
        )
        self.assertFalse(
            int_or_fade_validator('fade/50/-500', min_rule='1', max_rule='255', _type='wled')
        )

        # Should reject if target is non-integer
        self.assertFalse(
            int_or_fade_validator('fade/max/3600', min_rule='0', max_rule='1023', _type='pwm')
        )
        self.assertFalse(
            int_or_fade_validator('fade/max/3600', min_rule='1', max_rule='100', _type='bulb')
        )
        self.assertFalse(
            int_or_fade_validator('fade/max/3600', min_rule='1', max_rule='255', _type='wled')
        )

        # Should reject if missing _type kwarg (can't look up absolute lomits)
        self.assertEqual(
            int_or_fade_validator('fade/50/3600', min_rule='0', max_rule='1023'),
            'Instance missing required _type property'
        )

    def test_led_strip_rules(self):
        # Should accept int between min_rule and max_rule
        self.assertTrue(int_or_fade_validator(500, min_rule=0, max_rule=1023, _type='pwm'))

    def test_wled_rules(self):
        # Should accept int between min_rule and max_rule
        self.assertTrue(int_or_fade_validator(50, min_rule=1, max_rule=255, _type='wled'))

    def test_int_or_float_rules(self):
        # Should accept int or float
        self.assertTrue(int_or_float_validator(5))
        self.assertTrue(int_or_float_validator(5.0))
        self.assertTrue(int_or_float_validator(150000))
        self.assertTrue(int_or_float_validator(150000.0))

    def test_thermostat_rules(self):
        # Should accept Celsiues temperatures between 18 and 27 degrees
        self.assertTrue(thermostat_validator('20', units='celsius', mode='cool', tolerance='1'))
        # Should accept Kelvin temperatures between 291.15 and 300.15 degrees
        self.assertTrue(thermostat_validator('295', units='kelvin', mode='cool', tolerance='1'))
        # Should accept Fahrenheit temperatures between 65 and 80 degrees
        self.assertTrue(thermostat_validator('69', units='fahrenheit', mode='cool', tolerance='1'))


# Confirm functions in validators.py correctly reject invalid rules
class ValidatorErrorTests(TestCase):
    def setUp(self):
        # Load valid config
        self.config = load_unit_test_config()

    def test_invalid_type(self):
        # Verify error when type is unsupported
        invalid = self.config['device1']
        invalid['_type'] = 'foobar'
        self.assertEqual(validate_rules(invalid), 'Invalid type foobar')

    def test_invalid_rule_no_special_validator(self):
        # Verify error when failed to verify default-only rule
        invalid = self.config['device5']
        invalid['default_rule'] = '50'
        self.assertEqual(validate_rules(invalid), 'Screen: Invalid default rule 50')

    def test_api_target_non_dict_rule_string(self):
        # Should reject unless rule is dict with 2 keys
        self.assertFalse(api_target_validator("string that can't convert to dict"))
        self.assertFalse(api_target_validator(50))

    def test_api_target_dict_too_long(self):
        # Should reject after adding 3rd key
        invalid = self.config['device9']
        invalid['default_rule']['value'] = '50'
        self.assertFalse(api_target_validator(invalid))

    def test_api_target_invalid_key(self):
        # Should reject keys other than on and off
        invalid = self.config['device9']['default_rule']
        invalid['new'] = invalid['on'].copy()
        del invalid['on']
        self.assertFalse(api_target_validator(invalid))

    def test_api_target_invalid_non_list_subrule(self):
        # Keys (on and off) must contain list of parameters
        invalid = self.config['device9']['default_rule']
        invalid['on'] = 42
        self.assertFalse(api_target_validator(invalid))

    def test_api_target_invalid_ir_key_rule(self):
        # Create rule with ir_key command with invalid key
        invalid_rule = deepcopy(self.config['device9']['default_rule'])
        invalid_rule['on'][2] = 'fake_key'
        # Confirm rule is rejected
        self.assertFalse(api_target_validator(invalid_rule))

        # Create rule with ir_key command with invalid target
        invalid_rule = deepcopy(self.config['device9']['default_rule'])
        invalid_rule['on'][1] = 'fake_target'
        # Confirm rule is rejected
        self.assertFalse(api_target_validator(invalid_rule))

        # Sub-rule validator should return False if rule is not list
        self.assertFalse(is_valid_ir_api_call('ir_key/samsung_tv/power'))
        # Sub-rule validator should return False if first arg is not "ir_key"
        self.assertFalse(is_valid_ir_api_call(['ir', 'samsung_tv', 'power']))

    def test_invalid_bool_rule(self):
        # Confirm bool is rejected for correct types
        self.assertFalse(int_or_fade_validator(True, min_rule='0', max_rule='1023', _type='pwm'))
        self.assertFalse(int_or_fade_validator(True, min_rule='1', max_rule='100', _type='bulb'))
        self.assertFalse(int_or_fade_validator(True, min_rule='1', max_rule='255', _type='wled'))
        self.assertFalse(int_or_float_validator(True))
        self.assertFalse(int_or_float_validator(None))

    def test_invalid_out_of_range_rules(self):
        # Confirm range is enforced for correct types
        self.assertFalse(int_or_fade_validator('-50', min_rule='0', max_rule='1023', _type='pwm'))
        self.assertFalse(int_or_fade_validator('-50', min_rule='1', max_rule='100', _type='bulb'))
        self.assertFalse(int_or_fade_validator('-50', min_rule='1', max_rule='255', _type='wled'))
        self.assertFalse(thermostat_validator('30', tolerance=1, units='celsius', mode='cool'))
        self.assertFalse(thermostat_validator('320', tolerance=1, units='kelvin', mode='cool'))
        self.assertFalse(thermostat_validator('50', tolerance=1, units='fahrenheit', mode='cool'))

    def test_invalid_rule_limits(self):
        # Confirm correct error when max_rule greater than device limit
        self.assertEqual(
            int_or_fade_validator('50', min_rule='0', max_rule='4096', _type='pwm'),
            'Rule limits cannot be greater than 1023'
        )
        self.assertEqual(
            int_or_fade_validator('50', min_rule='1', max_rule='1000', _type='bulb'),
            'Rule limits cannot be greater than 100'
        )
        self.assertEqual(
            int_or_fade_validator('50', min_rule='1', max_rule='2000', _type='wled'),
            'Rule limits cannot be greater than 255'
        )

        # Confirm correct error when limits are string
        self.assertEqual(
            int_or_fade_validator('50', min_rule='0', max_rule='high', _type='pwm'),
            'Invalid rule limits, both must be int between 0 and 1023'
        )
        self.assertEqual(
            int_or_fade_validator('50', min_rule='1', max_rule='max', _type='bulb'),
            'Invalid rule limits, both must be int between 1 and 100'
        )
        self.assertEqual(
            int_or_fade_validator('50', min_rule='1', max_rule='bright', _type='wled'),
            'Invalid rule limits, both must be int between 1 and 255'
        )

    def test_thermostat_invalid_tolerance(self):
        # Confirm correct error for tolerance out of range
        self.assertEqual(
            thermostat_validator('70', tolerance='13', units='fahrenheit', mode='cool'),
            'Thermostat tolerance out of range (0.1 - 10.0)'
        )

        # Confirm correct error for string tolerance
        self.assertEqual(
            thermostat_validator('70', tolerance='low', units='fahrenheit', mode='cool'),
            'Thermostat tolerance must be int or float'
        )

        # Confirm correct error for missing tolerance
        self.assertEqual(
            thermostat_validator('70', units='fahrenheit', mode='cool'),
            'Thermostat missing required tolerance property'
        )

    def test_thermostat_invalid_mode(self):
        # Confirm correct error for invalid mode
        self.assertEqual(
            thermostat_validator('70', tolerance='1', units='fahrenheit', mode='measure'),
            'Thermostat mode must be either "heat" or "cool"'
        )

    def test_thermostat_invalid_units(self):
        # Confirm correct error for invalid temperature units
        self.assertEqual(
            thermostat_validator('70', tolerance='1', units='imperial', mode='cool'),
            'Thermostat units must be "fahrenheit", "celsius", or "kelvin"'
        )

    def test_invalid_noninteger_rules(self):
        # Confirm string is rejected for correct types
        self.assertFalse(int_or_fade_validator('max', min_rule='1', max_rule='255', _type='wled'))
        self.assertFalse(int_or_float_validator('max', min_rule='1', max_rule='100'))
        self.assertFalse(thermostat_validator('max', tolerance=1, units='fahrenheit', mode='cool'))

    def test_invalid_keyword_rules(self):
        # Confirm wrong keywords are rejected for correct types
        self.assertFalse(dummy_validator('max'))
        self.assertFalse(dummy_validator(50))

    def test_invalid_schedule_rules(self):
        # Confirm default error message works correctly
        self.config['device6']['min_rule'] = 500
        self.config['device6']['max_rule'] = 1000
        self.config['device6']['schedule']['01:00'] = 1023
        result = validate_rules(self.config['device6'])
        self.assertEqual(result, 'Cabinet Lights: Invalid schedule rule 1023')

        # Reset
        self.config['device6']['max_rule'] = 1023

        # Confirm correct error when schedule rule timestamp missing
        self.config['device6']['schedule'][''] = 1023
        result = validate_rules(self.config['device6'])
        self.assertEqual(result, 'Cabinet Lights: Missing schedule rule timestamp')

        # Confirm validators which return own error message work correctly
        # Placeholder, not currently possible

    # Original bug: Validators accepted "enabled" and "disabled" as valid
    # rules in all situations. Some device and sensor types do not support
    # these as default_rule, only as scheduled rules.
    # Fixed by refactor in c79864a9
    def test_regression_invalid_default_rule(self):
        # Set invalid default rules for all types that don't support
        self.config['device1']['default_rule'] = 'enabled'
        self.config['device2']['default_rule'] = 'disabled'
        self.config['device6']['default_rule'] = 'enabled'
        self.config['device8']['default_rule'] = 'disabled'
        self.config['device9']['default_rule'] = 'enabled'
        self.config['sensor1']['default_rule'] = 'disabled'
        self.config['sensor3']['default_rule'] = 'enabled'
        self.config['sensor5']['default_rule'] = 'disabled'

        # Validators should reject all with errors
        self.assertEqual(
            validate_rules(self.config['device1']),
            'Overhead: Invalid default rule enabled'
        )
        self.assertEqual(
            validate_rules(self.config['device2']),
            'Lamp: Invalid default rule disabled'
        )
        self.assertEqual(
            validate_rules(self.config['device6']),
            'Cabinet Lights: Invalid default rule enabled'
        )
        self.assertEqual(
            validate_rules(self.config['device8']),
            'TV Bias Lights: Invalid default rule disabled'
        )
        self.assertEqual(
            validate_rules(self.config['device9']),
            'Remote Control: Invalid default rule enabled'
        )
        self.assertEqual(
            validate_rules(self.config['sensor1']),
            'Motion: Invalid default rule disabled'
        )
        self.assertEqual(
            validate_rules(self.config['sensor3']),
            'Override: Invalid default rule enabled'
        )
        self.assertEqual(
            validate_rules(self.config['sensor5']),
            'Temperature: Invalid default rule disabled'
        )

    # Original bug: Validators for tplink and wled used hardcoded min/max
    # rules, ignoring min_rule and max_rule attributes.
    def test_regression_min_max_rule_ignored(self):
        self.assertFalse(int_or_fade_validator('1023', min_rule='500', max_rule='600', _type='pwm'))
        self.assertFalse(int_or_fade_validator('5', min_rule='25', max_rule='100', _type='bulb'))
        self.assertFalse(int_or_fade_validator('255', min_rule='1', max_rule='200', _type='wled'))

    # Original bug: Validators assumed min_rule + max_rule existed
    # in kwargs and did not trap error, resulting in exception if missing.
    def test_regression_missing_min_max_rule(self):
        # Delete required attributes
        del self.config['device1']['min_rule']
        del self.config['device2']['max_rule']
        del self.config['device6']['min_rule']
        del self.config['device8']['max_rule']
        del self.config['sensor5']['tolerance']

        self.assertEqual(
            validate_rules(self.config['device1']),
            'Instance missing required min_rule and/or max_rule property'
        )
        self.assertEqual(
            validate_rules(self.config['device2']),
            'Instance missing required min_rule and/or max_rule property'
        )
        self.assertEqual(
            validate_rules(self.config['device6']),
            'Instance missing required min_rule and/or max_rule property'
        )
        self.assertEqual(
            validate_rules(self.config['device8']),
            'Instance missing required min_rule and/or max_rule property'
        )
        self.assertEqual(
            validate_rules(self.config['sensor5']),
            'Thermostat missing required tolerance property'
        )

    # Original bug: Validators for Tplink and Wled require min/max args
    # but did not confirm that max is greater than min, resulting in all
    # rules being rejected with unhelpful errors.
    def test_regresstion_min_rule_greater_than_max_rule(self):
        # Set invalid limits
        self.config['device1']['min_rule'] = 100
        self.config['device1']['max_rule'] = 1
        self.config['device8']['min_rule'] = 255
        self.config['device8']['max_rule'] = 1

        # Confirm rejected with correct error
        self.assertEqual(
            validate_rules(self.config['device1']),
            'min_rule cannot be greater than max_rule'
        )
        self.assertEqual(
            validate_rules(self.config['device8']),
            'min_rule cannot be greater than max_rule'
        )

    # Original bug: int_or_float_validator only required float, allowing
    # NaN (which is a valid float, but breaks arithmetic) to be accepted.
    def test_regression_motion_sensor_accepts_nan(self):
        self.assertFalse(int_or_float_validator(float('NaN'), min_rule='1', max_rule='100'))
        self.assertFalse(int_or_float_validator(float('NaN')))

    # Original bug: int_or_float_validator cast rule to float in a conditional
    # and only returned True if the conditional passed. If rule was 0.0 (valid)
    # the conditional was not matched (0.0 == False) and nothing was returned.
    def test_regression_motion_sensor_returns_none_when_rule_is_0(self):
        self.assertTrue(int_or_float_validator(0))
        self.assertTrue(int_or_float_validator(0.0))

    # Original bug: int_or_float_validator cast rule to float and returned True
    # unless an exception was raised. If a boolean was passed it would be cast
    # to 1.0 or 0.0 and accepted incorrectly.
    def test_regression_int_or_float_validator_excepts_bool(self):
        self.assertFalse(int_or_float_validator(True))
        self.assertFalse(int_or_float_validator(False))
