# pylint: disable=line-too-long, missing-function-docstring, missing-module-docstring, missing-class-docstring

from unittest import TestCase
from validate_config import validate_full_config
from helper_functions import load_unit_test_config


# Test the validate_full_config function called before saving config to disk
class ValidateConfigTests(TestCase):
    def setUp(self):
        self.valid_config = load_unit_test_config()

    def test_valid_config(self):
        result = validate_full_config(self.valid_config)
        self.assertTrue(result)

    def test_missing_keys(self):
        del self.valid_config['metadata']['id']
        result = validate_full_config(self.valid_config)
        self.assertEqual(result, 'Missing required key in metadata section')

        del self.valid_config['metadata']
        result = validate_full_config(self.valid_config)
        self.assertEqual(result, 'Missing required top-level metadata key')

    def test_invalid_floor(self):
        self.valid_config['metadata']['floor'] = 'top'
        result = validate_full_config(self.valid_config)
        self.assertEqual(result, 'Invalid floor, must be integer')

    def test_duplicate_nicknames(self):
        self.valid_config['device4']['nickname'] = self.valid_config['device1']['nickname']
        result = validate_full_config(self.valid_config)
        self.assertEqual(result, 'Contains duplicate nicknames')

    def test_duplicate_pins(self):
        self.valid_config['sensor2']['pin'] = self.valid_config['sensor1']['pin']
        result = validate_full_config(self.valid_config)
        self.assertEqual(result, 'Contains duplicate pins')

    def test_invalid_device_pin(self):
        self.valid_config['device1']['pin'] = '14'
        result = validate_full_config(self.valid_config)
        self.assertEqual(
            result,
            f'Invalid device pin {self.valid_config["device1"]["pin"]} used'
        )

    def test_invalid_sensor_pin(self):
        self.valid_config['sensor1']['pin'] = '3'
        result = validate_full_config(self.valid_config)
        self.assertEqual(
            result,
            f'Invalid sensor pin {self.valid_config["sensor1"]["pin"]} used'
        )

    def test_noninteger_pin(self):
        self.valid_config['sensor1']['pin'] = 'three'
        result = validate_full_config(self.valid_config)
        self.assertEqual(result, 'Invalid pin (non-integer)')

    def test_invalid_device_type(self):
        self.valid_config['device1']['_type'] = 'nuclear'
        result = validate_full_config(self.valid_config)
        self.assertEqual(
            result,
            f'Invalid device type {self.valid_config["device1"]["_type"]} used'
        )

    def test_invalid_sensor_type(self):
        self.valid_config['sensor1']['_type'] = 'ozone-sensor'
        result = validate_full_config(self.valid_config)
        self.assertEqual(
            result,
            f'Invalid sensor type {self.valid_config["sensor1"]["_type"]} used'
        )

    def test_invalid_ip(self):
        self.valid_config['device1']['ip'] = '192.168.1.500'
        result = validate_full_config(self.valid_config)
        self.assertEqual(
            result,
            f'Invalid IP {self.valid_config["device1"]["ip"]}'
        )

    def test_thermostat_tolerance_out_of_range(self):
        self.valid_config['sensor5']['tolerance'] = 12.5
        result = validate_full_config(self.valid_config)
        self.assertEqual(result, 'Thermostat tolerance out of range (0.1 - 10.0)')

    def test_invalid_thermostat_tolerance(self):
        self.valid_config['sensor5']['tolerance'] = 'low'
        result = validate_full_config(self.valid_config)
        self.assertEqual(result, 'Thermostat tolerance must be int or float')

    def test_pwm_min_greater_than_max(self):
        self.valid_config['device6']['min_rule'] = 1023
        self.valid_config['device6']['max_rule'] = 500
        self.valid_config['device6']['default_rule'] = 700
        result = validate_full_config(self.valid_config)
        self.assertEqual(result, 'min_rule cannot be greater than max_rule')

    def test_pwm_limits_negative(self):
        self.valid_config['device6']['min_rule'] = -50
        self.valid_config['device6']['max_rule'] = -5
        result = validate_full_config(self.valid_config)
        self.assertEqual(result, 'Rule limits cannot be less than 0')

    def test_pwm_limits_over_max(self):
        self.valid_config['device6']['min_rule'] = 1023
        self.valid_config['device6']['max_rule'] = 4096
        result = validate_full_config(self.valid_config)
        self.assertEqual(result, 'Rule limits cannot be greater than 1023')

    def test_pwm_invalid_default_rule(self):
        self.valid_config['device6']['min_rule'] = 500
        self.valid_config['device6']['max_rule'] = 1000
        self.valid_config['device6']['default_rule'] = 1100
        result = validate_full_config(self.valid_config)
        self.assertEqual(result, 'Cabinet Lights: Invalid default rule 1100')

    def test_pwm_invalid_schedule_rule(self):
        self.valid_config['device6']['min_rule'] = 500
        self.valid_config['device6']['max_rule'] = 1000
        self.valid_config['device6']['schedule']['01:00'] = 1023
        result = validate_full_config(self.valid_config)
        self.assertEqual(result, 'Cabinet Lights: Invalid schedule rule 1023')

    def test_pwm_noninteger_limit(self):
        self.valid_config['device6']['min_rule'] = 'off'
        result = validate_full_config(self.valid_config)
        self.assertEqual(
            result,
            'Invalid rule limits, both must be int between 0 and 1023'
        )
