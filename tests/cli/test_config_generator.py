import os
from unittest import TestCase
from unittest.mock import patch, MagicMock
from questionary import ValidationError
from validate_config import validate_full_config
from helper_functions import load_unit_test_config
from config_generator import GenerateConfigFile, IntRange, FloatRange, MinLength, NicknameValidator
from config_rule_prompts import (
    api_call_prompt,
    api_target_schedule_rule_prompt,
    default_rule_prompt_router,
    schedule_rule_prompt_router,
    int_rule_prompt,
    float_rule_prompt,
    string_rule_prompt
)

# Get paths to test dir, CLI dir, repo dir
tests = os.path.dirname(os.path.realpath(__file__))
cli = os.path.split(tests)[0]
repo = os.path.dirname(cli)
test_config = os.path.join(repo, 'util', 'unit-test-config.json')

# Mock cli_config.json contents
mock_cli_config = {
    'nodes': {
        "node1": {
            "config": test_config,
            "ip": "192.168.1.123"
        },
        "node2": {
            "config": '/not/a/real/directory',
            "ip": "192.168.1.223"
        }
    },
    'webrepl_password': 'password',
    'config_directory': os.path.join(repo, 'config_files')
}


# Simulate user input object passed to validators
class SimulatedInput:
    def __init__(self, text):
        self.text = text


# Test input field validators
class TestValidators(TestCase):
    def test_int_range_validator(self):
        # Create validator accepting values between 1 and 100
        validator = IntRange(1, 100)

        # Should accept integers between 1 and 100
        user_input = SimulatedInput("2")
        self.assertTrue(validator.validate(user_input))
        user_input = SimulatedInput("75")
        self.assertTrue(validator.validate(user_input))

        # Should reject integers outside range
        user_input = SimulatedInput("999")
        with self.assertRaises(ValidationError):
            validator.validate(user_input)

        user_input = SimulatedInput("-5")
        with self.assertRaises(ValidationError):
            validator.validate(user_input)

        # Should reject string
        user_input = SimulatedInput("Fifty")
        with self.assertRaises(ValidationError):
            validator.validate(user_input)

    def test_float_range_validator(self):
        # Create validator accepting values between 1 and 100
        validator = FloatRange(1, 10)

        # Should accept integers and floats between 1 and 10
        user_input = SimulatedInput("2")
        self.assertTrue(validator.validate(user_input))
        user_input = SimulatedInput("5.5")
        self.assertTrue(validator.validate(user_input))
        user_input = SimulatedInput("10.0")
        self.assertTrue(validator.validate(user_input))

        # Should reject integers and floats outside range
        user_input = SimulatedInput("15")
        with self.assertRaises(ValidationError):
            validator.validate(user_input)

        user_input = SimulatedInput("-0.5")
        with self.assertRaises(ValidationError):
            validator.validate(user_input)

        # Should reject string
        user_input = SimulatedInput("Five")
        with self.assertRaises(ValidationError):
            validator.validate(user_input)

    def test_min_length_validator(self):
        # Create validator requiring at least 5 characters
        validator = MinLength(5)

        # Should accept strings with 5 or more characters
        user_input = SimulatedInput("String")
        self.assertTrue(validator.validate(user_input))
        user_input = SimulatedInput("12345")
        self.assertTrue(validator.validate(user_input))
        user_input = SimulatedInput("Super long string way longer than the minimum")
        self.assertTrue(validator.validate(user_input))

        # Should reject short strings, integers, etc
        user_input = SimulatedInput("x")
        with self.assertRaises(ValidationError):
            validator.validate(user_input)

        user_input = SimulatedInput(5)
        with self.assertRaises(ValidationError):
            validator.validate(user_input)

    def test_nickname_validator(self):
        # Create validator with 3 already-used nicknames
        validator = NicknameValidator(['Lights', 'Fan', 'Thermostat'])

        # Should accept unused nicknames
        user_input = SimulatedInput("Dimmer")
        self.assertTrue(validator.validate(user_input))
        user_input = SimulatedInput("Lamp")
        self.assertTrue(validator.validate(user_input))

        # Should reject already-used nicknames
        user_input = SimulatedInput("Lights")
        with self.assertRaises(ValidationError):
            validator.validate(user_input)

        # Should reject empty string
        user_input = SimulatedInput("")
        with self.assertRaises(ValidationError):
            validator.validate(user_input)


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
        self.assertEqual(result, f'Invalid device pin {self.valid_config["device1"]["pin"]} used')

    def test_invalid_sensor_pin(self):
        self.valid_config['sensor1']['pin'] = '3'
        result = validate_full_config(self.valid_config)
        self.assertEqual(result, f'Invalid sensor pin {self.valid_config["sensor1"]["pin"]} used')

    def test_noninteger_pin(self):
        self.valid_config['sensor1']['pin'] = 'three'
        result = validate_full_config(self.valid_config)
        self.assertEqual(result, 'Invalid pin (non-integer)')

    def test_invalid_device_type(self):
        self.valid_config['device1']['_type'] = 'nuclear'
        result = validate_full_config(self.valid_config)
        self.assertEqual(result, f'Invalid device type {self.valid_config["device1"]["_type"]} used')

    def test_invalid_sensor_type(self):
        self.valid_config['sensor1']['_type'] = 'ozone-sensor'
        result = validate_full_config(self.valid_config)
        self.assertEqual(result, f'Invalid sensor type {self.valid_config["sensor1"]["_type"]} used')

    def test_invalid_ip(self):
        self.valid_config['device1']['ip'] = '192.168.1.500'
        result = validate_full_config(self.valid_config)
        self.assertEqual(result, f'Invalid IP {self.valid_config["device1"]["ip"]}')

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
        self.assertEqual(result, 'Invalid rule limits, both must be int between 0 and 1023')


class TestGenerateConfigFile(TestCase):
    def setUp(self):
        # Create instance with mocked keywords
        self.generator = GenerateConfigFile()
        self.generator.schedule_keyword_options = ['sunrise', 'sunset']

        # Mock replaces .ask() method to simulate user input
        self.mock_ask = MagicMock()

    def test_run_prompt_method(self):
        # Mock all methods called by run_prompt, mock validator to return True
        with patch.object(self.generator, 'metadata_prompt') as mock_metadata_prompt, \
             patch.object(self.generator, 'add_devices_and_sensors') as mock_add_devices_and_sensors, \
             patch.object(self.generator, 'select_sensor_targets') as mock_select_sensor_targets, \
             patch.object(self.generator, 'finished_prompt') as mock_finished_prompt, \
             patch('config_generator.validate_full_config', return_value=True) as mock_validate_full_config:

            # Run method, confirm all mocks called
            self.generator.run_prompt()
            self.assertTrue(mock_metadata_prompt.called_once)
            self.assertTrue(mock_add_devices_and_sensors.called_once)
            self.assertTrue(mock_select_sensor_targets.called_once)
            self.assertTrue(mock_finished_prompt.called_once)
            self.assertTrue(mock_validate_full_config.called_once)

            # Confirm passed_validation set to True (mock)
            self.assertTrue(self.generator.passed_validation)

    def test_run_prompt_failed_validation(self):
        # Mock all methods called by run_prompt, mock validator to return False
        with patch.object(self.generator, 'metadata_prompt') as mock_metadata_prompt, \
             patch.object(self.generator, 'add_devices_and_sensors') as mock_add_devices_and_sensors, \
             patch.object(self.generator, 'select_sensor_targets') as mock_select_sensor_targets, \
             patch('config_generator.validate_full_config', return_value=False) as mock_validate_full_config:

            # Run method, confirm all mocks called
            self.generator.run_prompt()
            self.assertTrue(mock_metadata_prompt.called_once)
            self.assertTrue(mock_add_devices_and_sensors.called_once)
            self.assertTrue(mock_select_sensor_targets.called_once)
            self.assertTrue(mock_validate_full_config.called_once)

            # Confirm passed_validation set to False (mock)
            self.assertFalse(self.generator.passed_validation)

    def test_finished_prompt(self):
        # Simulate user selecting No
        self.mock_ask.unsafe_ask.return_value = 'No'
        with patch.object(self.generator, 'run_edit_prompt') as mock_run_edit_prompt, \
             patch('questionary.select', return_value=self.mock_ask):

            # Call method, confirm edit prompt was NOT called
            self.generator.finished_prompt()
            mock_run_edit_prompt.assert_not_called()

        # Simulate user selecting Yes
        self.mock_ask.unsafe_ask.return_value = 'Yes'
        with patch.object(self.generator, 'run_edit_prompt') as mock_run_edit_prompt, \
             patch('questionary.select', return_value=self.mock_ask):

            # Call method, confirm edit prompt WAS called
            self.generator.finished_prompt()
            mock_run_edit_prompt.assert_called_once()

    def test_metadata_prompt(self):
        # Mock responses to the ID, Floor, and Location prompts
        self.mock_ask.unsafe_ask.side_effect = ['Test ID', '2', 'Test Environment']
        with patch('questionary.text', return_value=self.mock_ask):
            self.generator.metadata_prompt()

        # Confirm responses added to correct keys in dict
        self.assertEqual(self.generator.config['metadata']['id'], 'Test ID')
        self.assertEqual(self.generator.config['metadata']['floor'], '2')
        self.assertEqual(self.generator.config['metadata']['location'], 'Test Environment')

    def test_sensor_type(self):
        self.mock_ask.unsafe_ask.return_value = 'MotionSensor'

        with patch('questionary.select', return_value=self.mock_ask):
            self.assertEqual(self.generator.sensor_type(), 'MotionSensor')

    def test_device_type(self):
        self.mock_ask.unsafe_ask.return_value = 'Dimmer'

        with patch('questionary.select', return_value=self.mock_ask):
            self.assertEqual(self.generator.device_type(), 'Dimmer')

    def test_nickname_prompt(self):
        # Add an already-used nickname
        self.generator.used_nicknames = ['Used']

        # Mock ask to return a different nickname
        self.mock_ask.unsafe_ask.return_value = 'Unused'
        with patch('questionary.text', return_value=self.mock_ask):
            # Confirm returns new nickname, new nickname added to used_nicknames
            response = self.generator.nickname_prompt()
            self.assertEqual(response, 'Unused')
            self.assertEqual(self.generator.used_nicknames, ['Used', 'Unused'])

    def test_add_devices_and_sensors_prompt(self):
        expected_device = {
            "_type": "dimmer",
            "nickname": "Overhead Lights",
            "ip": "192.168.1.123",
            "min_rule": "1",
            "max_rule": "100",
            "default_rule": "50",
            "schedule": {
                "10:00": "100",
                "20:00": "fade/25/3600",
                "00:00": "Disabled"
            }
        }

        expected_sensor = {
            "_type": "pir",
            "nickname": "Motion",
            "pin": "14",
            "default_rule": "5",
            "schedule": {
                "10:00": "5",
                "20:00": "1",
                "00:00": "Disabled"
            }
        }

        # Mock user input
        self.mock_ask.unsafe_ask.side_effect = [
            'Device',
            'Sensor',
            'Done'
        ]

        # Mock ask to return user input in expected order
        # Mock device and sensor prompts to return completed config objects
        with patch('questionary.select', return_value=self.mock_ask), \
             patch('questionary.text', return_value=self.mock_ask), \
             patch.object(self.generator, 'configure_device', return_value=expected_device), \
             patch.object(self.generator, 'configure_sensor', return_value=expected_sensor):

            # Run prompt
            self.generator.add_devices_and_sensors()

        # Confirm config sections added with correct keys
        self.assertEqual(self.generator.config['device1'], expected_device)
        self.assertEqual(self.generator.config['sensor1'], expected_sensor)

    def test_delete_devices_and_sensors(self):
        # Simulte user editing completed config
        self.generator.config = {
            "metadata": {
                "id": "Target Test",
                "floor": "1",
                "location": "Test Environment"
            },
            "device1": {
                "_type": "mosfet",
                "nickname": "Target1",
                "default_rule": "Enabled",
                "pin": "4",
                "schedule": {}
            },
            "device2": {
                "_type": "mosfet",
                "nickname": "Target2",
                "default_rule": "Enabled",
                "pin": "13",
                "schedule": {}
            },
            "sensor1": {
                "_type": "pir",
                "nickname": "Sensor",
                "pin": "5",
                "default_rule": "5",
                "schedule": {},
                "targets": []
            }
        }
        # Add pins and nicknames to used lists
        self.generator.used_pins = ["4", "13", "5"]
        self.generator.used_nicknames = ["Target1", "Target2", "Sensor"]

        # Mock user selecting both devices, run prompt
        self.mock_ask.unsafe_ask.return_value = ['Target1 (mosfet)', 'Target2 (mosfet)']
        with patch('questionary.checkbox', return_value=self.mock_ask):
            self.generator.delete_devices_and_sensors()
            self.assertTrue(self.mock_ask.called_once)

        # Confirm both devices were deleted
        self.assertEqual(list(self.generator.config.keys()), ["metadata", "sensor1"])

    def test_delete_devices_and_sensors_no_instances(self):
        # Simulate editing config with no devices or sensors
        self.generator.config = {
            "metadata": {
                "id": "Target Test",
                "floor": "1",
                "location": "Test Environment"
            }
        }

        # Call method with no mocks, should return immeditely
        self.generator.delete_devices_and_sensors()

    def test_configure_device_prompt(self):
        expected_output = {
            "_type": "dimmer",
            "nickname": "Overhead Lights",
            "ip": "192.168.1.123",
            "min_rule": "1",
            "max_rule": "100",
            "default_rule": "50",
            "schedule": {
                "10:00": "100",
                "20:00": "fade/25/3600",
                "00:00": "Disabled"
            }
        }

        # Mock ask to return parameters in expected order
        self.mock_ask.unsafe_ask.side_effect = [
            'TP Link Smart Dimmer',
            'Overhead Lights',
            '192.168.1.123',
            '1',
            '100',
            '50',
            'Yes',
            'Timestamp',
            '10:00',
            'Int',
            '100',
            'Yes',
            'Timestamp',
            '20:00',
            'Fade',
            '25',
            '3600',
            'Yes',
            'Timestamp',
            '00:00',
            'Disabled',
            'No'
        ]
        with patch('questionary.select', return_value=self.mock_ask), \
             patch('questionary.text', return_value=self.mock_ask):

            # Run prompt, confirm output matches expected
            config = self.generator.configure_device()
            self.assertEqual(config, expected_output)

            # Confirm nickname added to used list
            self.assertEqual(self.generator.used_nicknames, ['Overhead Lights'])

        # Repeat test with mosfet
        expected_output = {
            "_type": "mosfet",
            "nickname": "Mosfet",
            "default_rule": "Enabled",
            "pin": "4",
            "schedule": {}
        }

        # Mock ask to return parameters in expected order
        self.mock_ask.unsafe_ask.side_effect = [
            'Mosfet',
            'Mosfet',
            'Enabled',
            '4',
            'No'
        ]
        with patch('questionary.select', return_value=self.mock_ask), \
             patch('questionary.text', return_value=self.mock_ask):

            # Run prompt, confirm output matches expected
            config = self.generator.configure_device()
            self.assertEqual(config, expected_output)

            # Confirm nickname and pin added to used lists
            self.assertEqual(self.generator.used_nicknames, ['Overhead Lights', 'Mosfet'])
            self.assertEqual(self.generator.used_pins, ['4'])

    def test_configure_device_failed_validation(self):
        # Invalid config object with default_rule greater than max_rule
        invalid_config = {
            "_type": "dimmer",
            "nickname": "Overhead Lights",
            "ip": "192.168.1.123",
            "min_rule": "1",
            "max_rule": "50",
            "default_rule": "100",
            "schedule": {}
        }

        # Valid config expected after test complete
        valid_config = {
            '_type': 'dimmer',
            'nickname': 'Overhead Lights',
            'ip': '192.168.1.123',
            'min_rule': '1',
            'max_rule': '100',
            'default_rule': '50',
            'schedule': {}
        }

        # Mock ask to return user input in expected order
        self.mock_ask.unsafe_ask.side_effect = [
            'No',
            '192.168.1.123',
            '1',
            '100',
            '50',
            'No'
        ]

        # Mock ask to return user input in expected order
        with patch('questionary.select', return_value=self.mock_ask), \
             patch('questionary.text', return_value=self.mock_ask):

            # Pass invalid config to configure_device
            # Should prompt for schedule rules (No), fail validation,
            # go through reset_config_template, and be passed back to
            # configure_device again (remaining mock inputs)
            config = self.generator.configure_device(invalid_config)

        # Confirm valid config received after second loop
        self.assertEqual(config, valid_config)

    def test_configure_sensor_prompt(self):
        expected_output = {
            "_type": "pir",
            "nickname": "Motion",
            "pin": "14",
            "default_rule": "5",
            "schedule": {
                "10:00": "5",
                "20:00": "1",
                "00:00": "Disabled"
            },
            "targets": []
        }

        # Mock ask to return parameters in expected order
        self.mock_ask.unsafe_ask.side_effect = [
            'PIR Motion Sensor',
            'Motion',
            '5',
            '14',
            'Yes',
            'Timestamp',
            '10:00',
            'Float',
            '5',
            'Yes',
            'Timestamp',
            '20:00',
            'Float',
            '1',
            'Yes',
            'Timestamp',
            '00:00',
            'Disabled',
            'No'
        ]
        with patch('questionary.select', return_value=self.mock_ask), \
             patch('questionary.text', return_value=self.mock_ask):

            # Run prompt, confirm output matches expected
            config = self.generator.configure_sensor()
            self.assertEqual(config, expected_output)

            # Confirm nickname and pin added to used lists
            self.assertEqual(self.generator.used_nicknames, ['Motion'])
            self.assertEqual(self.generator.used_pins, ['14'])

        # Repeat test with thermostat
        expected_output = {
            "_type": "si7021",
            "nickname": "Thermostat",
            "default_rule": "70",
            "mode": "cool",
            "tolerance": "1.5",
            "units": "fahrenheit",
            "schedule": {
                "10:00": "75"
            },
            "targets": []
        }

        # Mock ask to return parameters in expected order
        self.mock_ask.unsafe_ask.side_effect = [
            'SI7021 Temperature Sensor',
            'Thermostat',
            'fahrenheit',
            '70',
            'cool',
            '1.5',
            'Yes',
            'Timestamp',
            '10:00',
            'Float',
            '75',
            'No'
        ]
        with patch('questionary.select', return_value=self.mock_ask), \
             patch('questionary.text', return_value=self.mock_ask):

            # Run prompt, confirm output matches expected
            config = self.generator.configure_sensor()
            self.assertEqual(config, expected_output)

            # Confirm nickname and pin added to used lists
            self.assertEqual(self.generator.used_nicknames, ['Motion', 'Thermostat'])
            self.assertEqual(self.generator.used_pins, ['14'])

    def test_configure_sensor_prompt_dummy(self):
        expected_output = {
            "_type": "dummy",
            "nickname": "Sunrise",
            "default_rule": "On",
            "schedule": {
                "06:00": "On",
                "20:00": "Off"
            },
            "targets": []
        }

        # Mock ask to return parameters in expected order
        self.mock_ask.unsafe_ask.side_effect = [
            'Dummy Sensor',
            'Sunrise',
            'On',
            'Yes',
            'Timestamp',
            '06:00',
            'On',
            'Yes',
            'Timestamp',
            '20:00',
            'Off',
            'No'
        ]
        with patch('questionary.select', return_value=self.mock_ask), \
             patch('questionary.text', return_value=self.mock_ask):

            # Run prompt, confirm output matches expected
            config = self.generator.configure_sensor()
            self.assertEqual(config, expected_output)

            # Confirm nickname and pin added to used lists
            self.assertEqual(self.generator.used_nicknames, ['Sunrise'])
            self.assertEqual(self.generator.used_pins, [])

    def test_configure_sensor_prompt_desktop(self):
        expected_output = {
            "_type": "desktop",
            "nickname": "Computer Activity",
            "ip": "192.168.1.123",
            "default_rule": "Enabled",
            "schedule": {
                "sunrise": "Enabled"
            },
            "targets": []
        }

        # Mock ask to return parameters in expected order
        self.mock_ask.unsafe_ask.side_effect = [
            'Computer Activity',
            'Computer Activity',
            'Enabled',
            '192.168.1.123',
            'Yes',
            'keyword',
            'sunrise',
            'Enabled',
            'No'
        ]
        with patch('questionary.select', return_value=self.mock_ask), \
             patch('questionary.text', return_value=self.mock_ask):

            # Run prompt, confirm output matches expected
            config = self.generator.configure_sensor()
            self.assertEqual(config, expected_output)

            # Confirm nickname and pin added to used lists
            self.assertEqual(self.generator.used_nicknames, ['Computer Activity'])
            self.assertEqual(self.generator.used_pins, [])

    def test_configure_sensor_prompt_load_cell(self):
        expected_output = {
            "_type": "load-cell",
            "nickname": "Bed Sensor",
            "default_rule": "10000",
            "pin_data": "18",
            "pin_clock": "19",
            "schedule": {
                "sunrise": "Disabled"
            },
            "targets": []
        }

        # Mock ask to return parameters in expected order
        self.mock_ask.unsafe_ask.side_effect = [
            'Load Cell Pressure Sensor',
            'Bed Sensor',
            '10000',
            '18',
            '19',
            'Yes',
            'keyword',
            'sunrise',
            'Disabled',
            'No'
        ]
        with patch('questionary.select', return_value=self.mock_ask), \
             patch('questionary.text', return_value=self.mock_ask):

            # Run prompt, confirm output matches expected
            config = self.generator.configure_sensor()
            self.assertEqual(config, expected_output)

            # Confirm nickname and pins added to used lists
            self.assertEqual(self.generator.used_nicknames, ['Bed Sensor'])
            self.assertEqual(self.generator.used_pins, ['18', '19'])

    def test_configure_sensor_failed_validation(self):
        # Invalid config object with unsupported default_rule
        invalid_config = {
            "_type": "dummy",
            "nickname": "Sunrise",
            "default_rule": "Enabled",
            "schedule": {},
            "targets": []
        }

        # Valid config expected after test complete
        valid_config = {
            "_type": "dummy",
            "nickname": "Sunrise",
            "default_rule": "On",
            "schedule": {},
            "targets": []
        }

        # Mock ask to return user input in expected order
        self.mock_ask.unsafe_ask.side_effect = [
            'No',
            'On',
            'No'
        ]

        # Mock ask to return user input in expected order
        with patch('questionary.select', return_value=self.mock_ask), \
             patch('questionary.text', return_value=self.mock_ask):

            # Pass invalid config to configure_device
            # Should prompt for schedule rules (No), fail validation,
            # go through reset_config_template, and be passed back to
            # configure_sensor again (remaining mock inputs)
            config = self.generator.configure_sensor(invalid_config)

        # Confirm valid config received after second loop
        self.assertEqual(config, valid_config)

    def test_reset_config_template(self):
        # Pass config with invalid values to reset_config_template
        invalid_config = {
            "_type": "si7021",
            "nickname": "Thermostat",
            "default_rule": "85",
            "mode": "cool",
            "tolerance": "11",
            "schedule": {
                "10:00": "75"
            }
        }
        reset_config = self.generator.reset_config_template(invalid_config)

        # Confirm correct properties reset to "placeholder"
        # Confirm schedule rules dict empty
        self.assertEqual(reset_config, {
            "_type": "si7021",
            "nickname": "Thermostat",
            "default_rule": "placeholder",
            "mode": "placeholder",
            "tolerance": "placeholder",
            "schedule": {}
        })

    def test_configure_ir_blaster(self):
        # Confirm no IR Blaster, confirm option in menu
        self.assertNotIn("ir_blaster", self.generator.config.keys())
        self.assertIn('IR Blaster', self.generator.category_options)

        expected_config = {
            'pin': '4',
            'target': [
                'ac',
                'tv'
            ],
            'macros': {}
        }

        # Mock user input
        self.mock_ask.unsafe_ask.side_effect = [
            'IR Blaster',
            '4',
            ['ac', 'tv'],
            'Done'
        ]

        # Mock ask to return user input in expected order
        # Select IR Blaster option, enter pin, select targets, select done
        with patch('questionary.select', return_value=self.mock_ask), \
             patch('questionary.checkbox', return_value=self.mock_ask):

            # Run prompt
            self.generator.add_devices_and_sensors()

        # Confirm added to config, selected pin in used_pins, IR option removed from menu
        self.assertEqual(self.generator.config['ir_blaster'], expected_config)
        self.assertIn('4', self.generator.used_pins)
        self.assertNotIn('IR Blaster', self.generator.category_options)

    def test_select_sensor_targets_prommpt(self):
        # Set partial config expected when user reaching targets prompt
        self.generator.config = {
            "metadata": {
                "id": "Target Test",
                "floor": "1",
                "location": "Test Environment"
            },
            "device1": {
                "_type": "mosfet",
                "nickname": "Target1",
                "default_rule": "Enabled",
                "pin": "4",
                "schedule": {}
            },
            "device2": {
                "_type": "mosfet",
                "nickname": "Target2",
                "default_rule": "Enabled",
                "pin": "13",
                "schedule": {}
            },
            "sensor1": {
                "_type": "pir",
                "nickname": "Sensor",
                "pin": "5",
                "default_rule": "5",
                "schedule": {},
                "targets": []
            }
        }

        # Mock responses to sensor target prompt
        self.mock_ask.unsafe_ask.return_value = ['Target1 (mosfet)', 'Target2 (mosfet)']
        with patch('questionary.checkbox', return_value=self.mock_ask):
            self.generator.select_sensor_targets()
            self.assertTrue(self.mock_ask.called_once)

        # Confirm both devices added to sensor targets
        self.assertEqual(self.generator.config['sensor1']['targets'], ['device1', 'device2'])

    def test_select_sensor_targets_no_targets(self):
        # Set partial config with no devices, only sensors
        self.generator.config = {
            "metadata": {
                "id": "Target Test",
                "floor": "1",
                "location": "Test Environment"
            },
            "sensor1": {
                "_type": "pir",
                "nickname": "Sensor",
                "pin": "5",
                "default_rule": "5",
                "schedule": {},
                "targets": []
            }
        }

        # Mock checkbox ask method, confirm nothing is called
        with patch('questionary.checkbox', return_value=self.mock_ask):
            self.generator.select_sensor_targets()
            self.assertFalse(self.mock_ask.called)

    def test_add_schedule_rule_keyword(self):
        # Simulate user reaching schedule rule prompt
        config = {
            "_type": "mosfet",
            "nickname": "Mosfet",
            "default_rule": "Enabled",
            "pin": "4",
            "schedule": {}
        }

        # Call schedule rule prompt with simulated user input
        self.mock_ask.unsafe_ask.side_effect = [
            'Keyword',
            'sunrise',
            'Enabled'
        ]
        with patch('questionary.select', return_value=self.mock_ask), \
             patch('questionary.text', return_value=self.mock_ask):

            # Confirm rule added successfully
            output = self.generator.add_schedule_rule(config)
            self.assertEqual(output['schedule'], {'sunrise': 'Enabled'})

    def test_add_schedule_rule_no_keywords_available(self):
        # Simulate no keywords in config file
        self.generator.schedule_keyword_options = []

        # Simulate user reaching schedule rule prompt
        config = {
            "_type": "mosfet",
            "nickname": "Mosfet",
            "default_rule": "Enabled",
            "pin": "4",
            "schedule": {}
        }

        # Call schedule rule prompt with simulated user input
        # Should not ask keyword or timestamp (no keywords available)
        self.mock_ask.unsafe_ask.side_effect = [
            '10:00',
            'Enabled'
        ]
        with patch('questionary.select', return_value=self.mock_ask), \
             patch('questionary.text', return_value=self.mock_ask):

            # Confirm rule added successfully
            output = self.generator.add_schedule_rule(config)
            self.assertEqual(output['schedule'], {'10:00': 'Enabled'})

    def test_api_target_ip_prompt(self):
        # Mock nodes.json contents
        self.generator.existing_nodes = mock_cli_config['nodes']

        # Simulate user selecting first option, confirm correct IP returned
        self.mock_ask.unsafe_ask.side_effect = ['node1']
        with patch('questionary.select', return_value=self.mock_ask):
            output = self.generator.apitarget_ip_prompt()
            self.assertEqual(output, '192.168.1.123')

    # Confirm the correct IP prompt is run when configuring ApiTarget
    def test_configure_device_api_target(self):
        # Partial config, block all prompts except IP and schedule
        config = {
            "_type": "api-target",
            "nickname": "API",
            "ip": "placeholder",
            "default_rule": {"on": ["ignore"], "off": ["ignore"]},
            "schedule": {}
        }

        # Simulate user declining schedule rule prompt
        self.mock_ask.unsafe_ask.side_effect = ['No']
        with patch('questionary.select', return_value=self.mock_ask), \
             patch.object(self.generator, 'apitarget_ip_prompt') as mock_ip_prompt:

            # Simulate user selecting first IP option
            mock_ip_prompt.return_value = '192.168.1.123'

            # Run prompt, confirm correct IP prompt is called
            self.generator.configure_device(config)
            self.assertTrue(mock_ip_prompt.called)

    def test_api_target_rule_prompt(self):
        # Mock nodes.json to include unit-test-config.json
        self.generator.existing_nodes = mock_cli_config['nodes']

        # Simulate user at rule prompt after selecting IP matching unit-test-config.json
        mock_config = {
            "_type": "api-target",
            "nickname": "API",
            "ip": "192.168.1.123",
            "default_rule": "placeholder",
            "schedule": {}
        }

        # Call API target rule prompt with simulated user input, confirm correct rule returned
        self.mock_ask.unsafe_ask.side_effect = [
            'API Call',
            True,
            'device1',
            'enable',
            True,
            'sensor1',
            'set_rule',
            'Float',
            '50'
        ]
        with patch('questionary.select', return_value=self.mock_ask), \
             patch('questionary.text', return_value=self.mock_ask), \
             patch('questionary.confirm', return_value=self.mock_ask), \
             patch('config_rule_prompts.get_existing_nodes', return_value=mock_cli_config['nodes']):

            rule = api_target_schedule_rule_prompt(mock_config)
            self.assertEqual(rule, {"on": ["enable", "device1"], "off": ["set_rule", "sensor1", "50"]})

        # Call again with simulated input selecting IR Blaster options, confirm correct rule returned
        self.mock_ask.unsafe_ask.side_effect = [
            'API Call',
            True,
            'IR Blaster',
            'tv',
            'power',
            False,
        ]
        with patch('questionary.select', return_value=self.mock_ask), \
             patch('questionary.text', return_value=self.mock_ask), \
             patch('questionary.confirm', return_value=self.mock_ask), \
             patch('config_rule_prompts.get_existing_nodes', return_value=mock_cli_config['nodes']):

            rule = api_target_schedule_rule_prompt(mock_config)
            self.assertEqual(rule, {"on": ["ir_key", "tv", "power"], "off": ["ignore"]})

        # Call schedule rule router with simulated input selecting 'Enabled' option
        self.mock_ask.unsafe_ask.side_effect = ['Enabled']
        with patch('questionary.select', return_value=self.mock_ask), \
             patch('questionary.text', return_value=self.mock_ask), \
             patch('questionary.confirm', return_value=self.mock_ask), \
             patch('config_rule_prompts.get_existing_nodes', return_value=mock_cli_config['nodes']):

            rule = schedule_rule_prompt_router(mock_config)
            self.assertEqual(rule, 'Enabled')

        # Call default rule router with simulated input selecting ignore option + endpoint requiring extra arg
        self.mock_ask.unsafe_ask.side_effect = [
            False,
            True,
            'sensor5',
            'enable_in',
            '1800'
        ]
        with patch('questionary.select', return_value=self.mock_ask), \
             patch('questionary.text', return_value=self.mock_ask), \
             patch('questionary.confirm', return_value=self.mock_ask), \
             patch('config_rule_prompts.get_existing_nodes', return_value=mock_cli_config['nodes']):

            rule = default_rule_prompt_router(mock_config)
            self.assertEqual(rule, {"on": ["ignore"], "off": ["enable_in", "sensor5", "1800"]})

    def test_api_call_prompt_target_config_missing(self):
        # Mock nodes.json to include node with fake config path
        self.generator.existing_nodes = mock_cli_config['nodes']

        # Confirm script exits with error when unable to open fake path
        with patch('config_rule_prompts.get_existing_nodes', return_value=mock_cli_config['nodes']):
            with self.assertRaises(SystemExit):
                api_call_prompt({'ip': '192.168.1.223'})

        # Confirm script exits with error when IP not in nodes.json
        with patch('config_rule_prompts.get_existing_nodes', return_value=mock_cli_config['nodes']):
            with self.assertRaises(SystemExit):
                api_call_prompt({'ip': '10.0.0.1'})

    def test_edit_existing_config(self):
        # Simulate user already completed all prompts
        self.generator.config = {
            "metadata": {
                "id": "Unit Test Existing Config",
                "floor": "0",
                "location": "Unit Test",
                "schedule_keywords": {
                    "morning": "11:30",
                    "relax": "23:00",
                    "sleep": "04:15",
                    "sunrise": "06:00",
                    "sunset": "18:00"
                }
            },
            "device1": {
                "_type": "mosfet",
                "nickname": "LED",
                "default_rule": "Enabled",
                "pin": "4",
                "schedule": {}
            },
            "sensor1": {
                "_type": "dummy",
                "nickname": "Sunrise",
                "default_rule": "On",
                "schedule": {
                    "sunrise": "Off",
                    "sunset": "On"
                },
                "targets": [
                    "device1"
                ]
            }
        }

        # Get path to config directory, create if doesn't exist
        config_directory = os.path.join(repo, 'config_files')
        if not os.path.exists(config_directory):
            os.mkdir(config_directory)

        # Mock get_cli_config to return config directory path, write to disk
        with patch('config_generator.get_cli_config', return_value={'config_directory': config_directory}):
            self.generator.write_to_disk()

        # Confirm file exists
        path = os.path.join(config_directory, 'unit-test-existing-config.json')
        self.assertTrue(os.path.exists(path))

        # Instantiate new generator with path to existing config, confirm edit_mode and config attributes
        generator = GenerateConfigFile(path)
        self.assertTrue(generator.edit_mode)
        self.assertEqual(generator.config, self.generator.config)

        # Simulate user selecting each option in edit prompt
        self.mock_ask.unsafe_ask.side_effect = [
            'Edit metadata',
            'Add devices and sensors',
            'Delete devices and sensors',
            'Edit sensor targets',
            'Done'
        ]

        # Mock all methods called by run_edit_prompt, mock validator to return True
        with patch.object(generator, 'metadata_prompt') as mock_metadata_prompt, \
             patch.object(generator, 'add_devices_and_sensors') as mock_add_devices_and_sensors, \
             patch.object(generator, 'delete_devices_and_sensors') as mock_delete_devices_and_sensors, \
             patch.object(generator, 'select_sensor_targets') as mock_select_sensor_targets, \
             patch('config_generator.validate_full_config', return_value=True) as mock_validate_full_config, \
             patch('questionary.select', return_value=self.mock_ask):

            # Run prompt, confirm all mocks called
            generator.run_prompt()
            self.assertTrue(mock_metadata_prompt.called_once)
            self.assertTrue(mock_add_devices_and_sensors.called_once)
            self.assertTrue(mock_delete_devices_and_sensors.called_once)
            self.assertTrue(mock_select_sensor_targets.called_once)
            self.assertTrue(mock_validate_full_config.called_once)

            # Confirm prompt methods were called with default values from existing config
            self.assertEqual(mock_metadata_prompt.call_args_list[0][0], ("Unit Test Existing Config", "0", "Unit Test"))

            # Confirm passed_validation set to True (mock)
            self.assertTrue(generator.passed_validation)

        # Delete test config
        os.remove(path)

    def test_edit_invalid_config_path(self):
        # Create non-json config file
        with open('fake_config_file.txt', 'w'):
            pass

        # Attempt to instantiate with non-json config file, confirm raises error
        with self.assertRaises(SystemExit):
            GenerateConfigFile('/does/not/exist.json')

        # Attempt to instantiate with invalid path, confirm raises error
        with self.assertRaises(SystemExit):
            GenerateConfigFile('/does/not/exist')

        # Delete fake config
        os.remove('fake_config_file.txt')


class TestRegressions(TestCase):
    def setUp(self):
        # Create instance with mocked keywords
        self.generator = GenerateConfigFile()
        self.generator.schedule_keyword_options = ['sunrise', 'sunset']

        # Mock replaces .ask() method to simulate user input
        self.mock_ask = MagicMock()

    # Original bug: Thermostat option remained in menu after adding to config,
    # allowing user to configure multiple thermostats (not supported)
    def test_prevent_multiple_thermostats(self):
        sensor_config = {
            "_type": "si7021",
            "nickname": "Thermostat",
            "default_rule": "70",
            "mode": "cool",
            "tolerance": "1.5",
            "units": "fahrenheit",
            "schedule": {
                "10:00": "75"
            },
            "targets": []
        }

        # Mock ask to return parameters in expected order
        self.mock_ask.unsafe_ask.side_effect = [
            'SI7021 Temperature Sensor',
            'Thermostat',
            'fahrenheit',
            '70',
            'cool',
            '1.5',
            'Yes',
            'Timestamp',
            '10:00',
            'Float',
            '75',
            'No'
        ]
        with patch('questionary.select', return_value=self.mock_ask) as mock_select, \
             patch('questionary.text', return_value=self.mock_ask):

            # Run prompt, confirm output matches expected
            self.generator.config['sensor1'] = self.generator.configure_sensor()
            self.assertEqual(self.generator.config['sensor1'], sensor_config)

        # Simulate user attempting to add a duplicate SI7021
        self.mock_ask.unsafe_ask.side_effect = ['SI7021 Temperature Sensor']
        with patch('questionary.select', return_value=self.mock_ask) as mock_select:
            # Run sensor type select prompt
            self.generator.sensor_type()

            # Confirm SI7021 was NOT in options list
            _, kwargs = mock_select.call_args
            self.assertFalse('SI7021 Temperature Sensor' in kwargs['choices'])

    # Original bug: SI7021 was removed from sensor options after first instance
    # added, but was not removed when editing an existing config that contained
    # an SI7021. This allowed the user to configure multiple (not supported).
    def test_prevent_multiple_thermostats_edit_existing(self):
        # Simulate user already completed all prompts, added si7021
        self.generator.config = {
            "metadata": {
                "id": "Unit Test Existing Config",
                "floor": "0",
                "location": "Unit Test",
                "schedule_keywords": {
                    "morning": "11:30",
                    "relax": "23:00",
                    "sleep": "04:15",
                    "sunrise": "06:00",
                    "sunset": "18:00"
                }
            },
            "sensor1": {
                "_type": "si7021",
                "nickname": "Thermostat",
                "default_rule": "70",
                "mode": "cool",
                "tolerance": "1.5",
                "units": "fahrenheit",
                "schedule": {},
                "targets": []
            }
        }

        # Get path to config directory, create if doesn't exist
        config_directory = os.path.join(repo, 'config_files')
        if not os.path.exists(config_directory):
            os.mkdir(config_directory)

        # Mock get_cli_config to return config directory path, write to disk
        with patch('config_generator.get_cli_config', return_value={'config_directory': config_directory}):
            self.generator.write_to_disk()

        # Confirm file exists
        path = os.path.join(config_directory, 'unit-test-existing-config.json')
        self.assertTrue(os.path.exists(path))

        # Instantiate new generator with path to existing config (simulate editing)
        generator = GenerateConfigFile(path)
        # Confirm edit_mode and config attributes
        self.assertTrue(generator.edit_mode)
        self.assertEqual(generator.config, self.generator.config)

        # Simulate user attempting to add a duplicate SI7021
        self.mock_ask.unsafe_ask.side_effect = ['SI7021 Temperature Sensor']
        with patch('questionary.select', return_value=self.mock_ask) as mock_select:
            # Run sensor type select prompt
            generator.sensor_type()

            # Confirm SI7021 was NOT in options list
            _, kwargs = mock_select.call_args
            self.assertFalse('SI7021 Temperature Sensor' in kwargs['choices'])

        # Delete test config
        os.remove(path)

    # Original bug: Selecting SI7021 permanently removed the option from sensor
    # type options. If user changed mind and deleted SI7021 the option would
    # not reappear, making it impossible to configure without starting over.
    def test_allow_si7021_after_removing_existing_si7021(self):
        # Simulate user already completed all prompts, added si7021
        self.generator.config = {
            "metadata": {
                "id": "Unit Test Existing Config",
                "floor": "0",
                "location": "Unit Test",
                "schedule_keywords": {
                    "morning": "11:30",
                    "relax": "23:00",
                    "sleep": "04:15",
                    "sunrise": "06:00",
                    "sunset": "18:00"
                }
            },
            "sensor1": {
                "_type": "si7021",
                "nickname": "Thermostat",
                "default_rule": "70",
                "mode": "cool",
                "tolerance": "1.5",
                "units": "fahrenheit",
                "schedule": {},
                "targets": []
            }
        }

        # Get path to config directory, create if doesn't exist
        config_directory = os.path.join(repo, 'config_files')
        if not os.path.exists(config_directory):
            os.mkdir(config_directory)

        # Mock get_cli_config to return config directory path, write to disk
        with patch('config_generator.get_cli_config', return_value={'config_directory': config_directory}):
            self.generator.write_to_disk()

        # Confirm file exists
        path = os.path.join(config_directory, 'unit-test-existing-config.json')
        self.assertTrue(os.path.exists(path))

        # Instantiate new generator with path to existing config, confirm edit_mode and config attributes
        generator = GenerateConfigFile(path)
        self.assertTrue(generator.edit_mode)
        self.assertEqual(generator.config, self.generator.config)

        # Mock user deleting existing SI7021 sensor
        self.mock_ask.unsafe_ask.return_value = ['Thermostat (si7021)']
        with patch('questionary.checkbox', return_value=self.mock_ask):
            generator.delete_devices_and_sensors()
            self.assertTrue(self.mock_ask.called_once)

        # Mock user adding another si7021 (option should reappear)
        self.mock_ask.unsafe_ask.side_effect = [
            'SI7021 Temperature Sensor',
            'Thermostat',
            'fahrenheit',
            '70',
            'cool',
            '1.5',
            'No'
        ]
        with patch('questionary.select', return_value=self.mock_ask) as mock_select, \
             patch('questionary.text', return_value=self.mock_ask):

            # Run prompt
            generator.config['sensor1'] = generator.configure_sensor()

            # Confirm SI7021 option appeared (config no longer contains si7021)
            _, kwargs = mock_select.call_args
            self.assertFalse('SI7021 Temperature Sensor' in kwargs['choices'])

    # Original bug: IntRange was used for PIR and Thermostat rules, preventing
    # float rules from being configured. Now uses FloatRange.
    def test_wrong_rule_type(self):
        # Simulate user at rule prompt after selecting thermostat
        mock_config = {
            "_type": "si7021",
            "nickname": "Thermostat",
            "default_rule": "placeholder",
            "mode": "cool",
            "tolerance": "placeholder",
            "schedule": {},
            "targets": []
        }

        # Call default rule router with simulated float rule input
        self.mock_ask.unsafe_ask.side_effect = ['69.5']
        with patch('questionary.text', return_value=self.mock_ask), \
             patch('config_rule_prompts.IntRange') as mock_int_range, \
             patch('config_rule_prompts.FloatRange') as mock_float_range:

            # Confirm FloatRange called, IntRange not called
            rule = default_rule_prompt_router(mock_config)
            self.assertEqual(rule, '69.5')
            self.assertTrue(mock_float_range.called)
            self.assertFalse(mock_int_range.called)

        # Call schedule rule router with simulated float rule input
        self.mock_ask.unsafe_ask.side_effect = ['Float', '69.5']
        with patch('questionary.select', return_value=self.mock_ask), \
             patch('questionary.text', return_value=self.mock_ask), \
             patch('config_rule_prompts.IntRange') as mock_int_range, \
             patch('config_rule_prompts.FloatRange') as mock_float_range:

            # Confirm FloatRange called, IntRange not called
            rule = schedule_rule_prompt_router(mock_config)
            self.assertEqual(rule, '69.5')
            self.assertTrue(mock_float_range.called)
            self.assertFalse(mock_int_range.called)

        # Repeat both tests with motion sensor
        mock_config = {
            "_type": "pir",
            "nickname": "Motion",
            "default_rule": "placeholder",
            "pin": "4",
            "schedule": {},
            "targets": []
        }

        # Call default rule router with simulated float rule input
        self.mock_ask.unsafe_ask.side_effect = ['5.5']
        with patch('questionary.text', return_value=self.mock_ask), \
             patch('config_rule_prompts.IntRange') as mock_int_range, \
             patch('config_rule_prompts.FloatRange') as mock_float_range:

            # Confirm FloatRange called, IntRange not called
            rule = default_rule_prompt_router(mock_config)
            self.assertEqual(rule, '5.5')
            self.assertTrue(mock_float_range.called)
            self.assertFalse(mock_int_range.called)

        # Call schedule rule router with simulated float rule input
        self.mock_ask.unsafe_ask.side_effect = ['Float', '5.5']
        with patch('questionary.select', return_value=self.mock_ask), \
             patch('questionary.text', return_value=self.mock_ask), \
             patch('config_rule_prompts.IntRange') as mock_int_range, \
             patch('config_rule_prompts.FloatRange') as mock_float_range:

            # Confirm FloatRange called, IntRange not called
            rule = schedule_rule_prompt_router(mock_config)
            self.assertEqual(rule, '5.5')
            self.assertTrue(mock_float_range.called)
            self.assertFalse(mock_int_range.called)

    # Original bug: When devices/sensors were deleted their pins and nicknames
    # were not removed from used_pins and used_nicknames, preventing the user
    # from selecting them again
    def test_unusable_pin_and_nicknames(self):
        # Set partial config with 3 used pins and nicknames
        self.generator.config = {
            "metadata": {
                "id": "Target Test",
                "floor": "1",
                "location": "Test Environment"
            },
            "device1": {
                "_type": "mosfet",
                "nickname": "Target1",
                "default_rule": "Enabled",
                "pin": "4",
                "schedule": {}
            },
            "device2": {
                "_type": "mosfet",
                "nickname": "Target2",
                "default_rule": "Enabled",
                "pin": "13",
                "schedule": {}
            },
            "sensor1": {
                "_type": "pir",
                "nickname": "Sensor",
                "pin": "5",
                "default_rule": "5",
                "schedule": {},
                "targets": []
            }
        }
        # Add pins and nicknames to used lists
        self.generator.used_pins = ["4", "13", "5"]
        self.generator.used_nicknames = ["Target1", "Target2", "Sensor"]

        # Mock user deleting all devices and sensors, run prompt
        self.mock_ask.unsafe_ask.return_value = ['Target1 (mosfet)', 'Target2 (mosfet)', 'Sensor (pir)']
        with patch('questionary.checkbox', return_value=self.mock_ask):
            self.generator.delete_devices_and_sensors()
            self.assertTrue(self.mock_ask.called_once)

        # Confirm used pins and nickname lists are now empty
        self.assertEqual(self.generator.used_pins, [])
        self.assertEqual(self.generator.used_nicknames, [])


class TestRulePrompts(TestCase):
    def setUp(self):
        # Mock replaces .ask() method to simulate user input
        self.mock_ask = MagicMock()

    def test_int_rule_prompt(self):
        # Create mock config object with min/max rules
        config = {
            'min_rule': '1',
            'max_rule': '100'
        }

        # Mock user input for default rule
        self.mock_ask.unsafe_ask.return_value = '90'

        # Run default prompt with mocked user input, confirm return value
        with patch('questionary.text', return_value=self.mock_ask):
            rule = int_rule_prompt(config, "default")
            self.assertEqual(rule, '90')

        # Mock user input for schedule rule
        self.mock_ask.unsafe_ask.return_value = 'Enabled'

        # Run schedule prompt with mocked user input, confirm return value
        with patch('questionary.select', return_value=self.mock_ask):
            rule = int_rule_prompt(config, "schedule")
            self.assertEqual(rule, 'Enabled')

        # Mock user input for schedule rule
        self.mock_ask.unsafe_ask.side_effect = ['Int', '50']

        # Run schedule prompt with mocked user input, confirm return value
        with patch('questionary.select', return_value=self.mock_ask), \
             patch('questionary.text', return_value=self.mock_ask):
            rule = int_rule_prompt(config, "schedule")
            self.assertEqual(rule, '50')

    def test_float_rule_prompt(self):
        # Create mock config object with thermostat parameters
        config = {
            '_type': 'dht22',
            'units': 'fahrenheit'
        }

        # Mock user input for default rule
        self.mock_ask.unsafe_ask.return_value = '70'

        # Run default prompt with mocked user input, confirm return value
        with patch('questionary.text', return_value=self.mock_ask):
            rule = float_rule_prompt(config, "default")
            self.assertEqual(rule, '70')

        # Mock user input for standard schedule rule
        self.mock_ask.unsafe_ask.return_value = 'Enabled'

        # Run schedule prompt with mocked user input, confirm return value
        with patch('questionary.select', return_value=self.mock_ask):
            rule = float_rule_prompt(config, "schedule")
            self.assertEqual(rule, 'Enabled')

        # Change units to kelvin, mock user input for schedule rule
        config['units'] = 'kelvin'
        self.mock_ask.unsafe_ask.side_effect = ['Float', '300']

        # Run schedule prompt with mocked user input, confirm return value
        with patch('questionary.select', return_value=self.mock_ask), \
             patch('questionary.text', return_value=self.mock_ask):
            rule = float_rule_prompt(config, "schedule")
            self.assertEqual(rule, '300')

    def test_string_rule_prompt(self):
        # Mock user input for default rule
        self.mock_ask.unsafe_ask.return_value = 'http://192.168.1.123:8123/endpoint'

        # Run default prompt with mocked user input, confirm return value
        with patch('questionary.text', return_value=self.mock_ask):
            rule = string_rule_prompt({}, "default")
            self.assertEqual(rule, 'http://192.168.1.123:8123/endpoint')

        # Mock user input for schedule rule
        self.mock_ask.unsafe_ask.return_value = 'Enabled'

        # Run schedule prompt with mocked user input, confirm return value
        with patch('questionary.select', return_value=self.mock_ask):
            rule = string_rule_prompt({}, "schedule")
            self.assertEqual(rule, 'Enabled')

        # Mock user input for schedule rule
        self.mock_ask.unsafe_ask.side_effect = ['String', 'http://192.168.1.123:8123/endpoint']

        # Run schedule prompt with mocked user input, confirm return value
        with patch('questionary.select', return_value=self.mock_ask), \
             patch('questionary.text', return_value=self.mock_ask):
            rule = string_rule_prompt({}, "schedule")
            self.assertEqual(rule, 'http://192.168.1.123:8123/endpoint')
