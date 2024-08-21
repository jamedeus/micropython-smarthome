# pylint: disable=line-too-long, missing-function-docstring, missing-module-docstring, missing-class-docstring, protected-access

import os
from unittest import TestCase
from unittest.mock import patch, MagicMock
from questionary import ValidationError
from validation_constants import valid_device_pins
from config_generator import GenerateConfigFile, main
from config_prompt_validators import (
    IntRange,
    FloatRange,
    MinLength,
    LengthRange,
    NicknameValidator
)
from config_rule_prompts import (
    api_call_prompt,
    api_target_schedule_rule_prompt,
    default_rule_prompt_router,
    schedule_rule_prompt_router,
    int_rule_prompt,
    float_rule_prompt,
    string_rule_prompt
)
from validation_constants import (
    valid_device_pins,
    valid_sensor_pins
)
from mock_cli_config import mock_cli_config


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
        self.assertTrue(validator.validate(SimulatedInput("2")))
        self.assertTrue(validator.validate(SimulatedInput("75")))

        # Should reject integers outside range
        with self.assertRaises(ValidationError):
            validator.validate(SimulatedInput("999"))

        with self.assertRaises(ValidationError):
            validator.validate(SimulatedInput("-5"))

        # Should reject string
        with self.assertRaises(ValidationError):
            validator.validate(SimulatedInput("Fifty"))

    def test_float_range_validator(self):
        # Create validator accepting values between 1 and 100
        validator = FloatRange(1, 10)

        # Should accept integers and floats between 1 and 10
        self.assertTrue(validator.validate(SimulatedInput("2")))
        self.assertTrue(validator.validate(SimulatedInput("5.5")))
        self.assertTrue(validator.validate(SimulatedInput("10.0")))

        # Should reject integers and floats outside range
        with self.assertRaises(ValidationError):
            validator.validate(SimulatedInput("15"))

        with self.assertRaises(ValidationError):
            validator.validate(SimulatedInput("-0.5"))

        # Should reject string
        with self.assertRaises(ValidationError):
            validator.validate(SimulatedInput("Five"))

    def test_min_length_validator(self):
        # Create validator requiring at least 5 characters
        validator = MinLength(5)

        # Should accept strings with 5 or more characters
        self.assertTrue(validator.validate(SimulatedInput("String")))
        self.assertTrue(validator.validate(SimulatedInput("12345")))
        self.assertTrue(validator.validate(SimulatedInput(
            "Super long string way longer than the minimum"
        )))

        # Should reject short strings, integers, etc
        with self.assertRaises(ValidationError):
            validator.validate(SimulatedInput("x"))

        with self.assertRaises(ValidationError):
            validator.validate(SimulatedInput(5))

    def test_length_range_validator(self):
        # Create validator requiring between 4 and 9 characters
        validator = LengthRange(4, 9)

        # Should accept strings with 4-9 characters
        self.assertTrue(validator.validate(SimulatedInput("1234")))
        self.assertTrue(validator.validate(SimulatedInput("12345")))
        self.assertTrue(validator.validate(SimulatedInput("123456")))
        self.assertTrue(validator.validate(SimulatedInput("1234567")))
        self.assertTrue(validator.validate(SimulatedInput("12345678")))
        self.assertTrue(validator.validate(SimulatedInput("123456789")))

        # Should reject strings with fewer than 4 or greater than 9 characters
        with self.assertRaises(ValidationError):
            self.assertFalse(validator.validate(SimulatedInput("123")))
        with self.assertRaises(ValidationError):
            self.assertFalse(validator.validate(SimulatedInput("1234567890")))

        # Should reject integers
        with self.assertRaises(ValidationError):
            validator.validate(SimulatedInput(5))

    def test_nickname_validator(self):
        # Create validator with 3 already-used nicknames
        validator = NicknameValidator(['Lights', 'Fan', 'Thermostat'])

        # Should accept unused nicknames
        self.assertTrue(validator.validate(SimulatedInput("Dimmer")))
        self.assertTrue(validator.validate(SimulatedInput("Lamp")))

        # Should reject already-used nicknames
        with self.assertRaises(ValidationError):
            validator.validate(SimulatedInput("Lights"))

        # Should reject empty string
        with self.assertRaises(ValidationError):
            validator.validate(SimulatedInput(""))


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
        self.mock_ask.unsafe_ask.side_effect = [
            'String',
            'http://192.168.1.123:8123/endpoint'
        ]

        # Run schedule prompt with mocked user input, confirm return value
        with patch('questionary.select', return_value=self.mock_ask), \
             patch('questionary.text', return_value=self.mock_ask):
            rule = string_rule_prompt({}, "schedule")
            self.assertEqual(rule, 'http://192.168.1.123:8123/endpoint')


class TestGenerateConfigFile(TestCase):
    def setUp(self):
        # Create instance with mocked keywords
        self.generator = GenerateConfigFile()
        self.generator.schedule_keyword_options = ['sunrise', 'sunset']

        # Mock replaces .ask() method to simulate user input
        self.mock_ask = MagicMock()

    @classmethod
    def tearDownClass(cls):
        # Delete unit-test-existing-config.json from disk if it still exists
        path = os.path.join(
            mock_cli_config['config_directory'],
            'unit-test-existing-config.json'
        )
        if os.path.exists(path):
            os.remove(path)
        # Delete fake_config_file.txt from disk if it still exists
        if os.path.exists('fake_config_file.txt'):
            os.remove('fake_config_file.txt')

    def test_run_prompt_method(self):
        # Mock all methods called by run_prompt, mock validator to return True
        with patch.object(self.generator, 'metadata_prompt') as mock_metadata_prompt, \
             patch.object(self.generator, 'add_devices_and_sensors') as mock_add_devices_and_sensors, \
             patch.object(self.generator, 'select_sensor_targets') as mock_select_sensor_targets, \
             patch.object(self.generator, '_GenerateConfigFile__finished_prompt') as mock_finished_prompt, \
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
            self.generator._GenerateConfigFile__finished_prompt()
            mock_run_edit_prompt.assert_not_called()

        # Simulate user selecting Yes
        self.mock_ask.unsafe_ask.return_value = 'Yes'
        with patch.object(self.generator, 'run_edit_prompt') as mock_run_edit_prompt, \
             patch('questionary.select', return_value=self.mock_ask):

            # Call method, confirm edit prompt WAS called
            self.generator._GenerateConfigFile__finished_prompt()
            mock_run_edit_prompt.assert_called_once()

    def test_metadata_prompt(self):
        # Mock responses to the ID, Floor, and Location prompts
        self.mock_ask.unsafe_ask.side_effect = ['Test ID', '2', 'Test Environment']
        with patch('questionary.text', return_value=self.mock_ask):
            self.generator.metadata_prompt()

        # Confirm responses added to correct keys in dict
        metadata = self.generator.config['metadata']
        self.assertEqual(metadata['id'], 'Test ID')
        self.assertEqual(metadata['floor'], '2')
        self.assertEqual(metadata['location'], 'Test Environment')

    def test_sensor_type(self):
        self.mock_ask.unsafe_ask.return_value = 'MotionSensor'

        with patch('questionary.select', return_value=self.mock_ask):
            self.assertEqual(
                self.generator._GenerateConfigFile__sensor_type(),
                'MotionSensor'
            )

    def test_device_type(self):
        self.mock_ask.unsafe_ask.return_value = 'Dimmer'

        with patch('questionary.select', return_value=self.mock_ask):
            self.assertEqual(
                self.generator._GenerateConfigFile__device_type(),
                'Dimmer'
            )

    def test_nickname_prompt(self):
        # Simulate mock config with several nicknames
        self.generator.config = {
            "device1": {
                "nickname": "Target1"
            },
            "device2": {
                "nickname": "Target2"
            },
            "sensor1": {
                "nickname": "Sensor"
            }
        }

        # Mock ask to return a different nickname
        self.mock_ask.unsafe_ask.return_value = 'Unused'
        with patch('questionary.text', return_value=self.mock_ask), \
             patch('config_generator.NicknameValidator') as mock_validator:

            # Confirm returns user selected nickname
            response = self.generator._GenerateConfigFile__nickname_prompt()
            self.assertEqual(response, 'Unused')

            # Confirm validator received list of all existing nicknames
            mock_validator.assert_called_with(
                ['Target1', 'Target2', 'Sensor']
            )

    def test_pin_prompt(self):
        # Simulate mock config with several pins selected
        self.generator.config = {
            "device1": {
                "pin": "4"
            },
            "device2": {
                "pin": "13"
            },
            "sensor1": {
                "pin": "19"
            },
            "sensor2": {
                "pin": "32"
            },
            "ir_blaster": {
                "pin": "27"
            }
        }

        # Mock ask to return a different pin
        self.mock_ask.unsafe_ask.return_value = '21'
        with patch('questionary.select', return_value=self.mock_ask) as mock_select:
            # Confirm returns user selected pin
            response = self.generator._GenerateConfigFile__pin_prompt(valid_device_pins)
            self.assertEqual(response, '21')

            # Confirm options did not include any existing pins
            _, kwargs = mock_select.call_args
            self.assertEqual(
                kwargs['choices'],
                ['16', '17', '18', '21', '22', '23', '25', '26', '33']
            )

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
             patch.object(self.generator, '_GenerateConfigFile__configure_device', return_value=expected_device), \
             patch.object(self.generator, '_GenerateConfigFile__configure_sensor', return_value=expected_sensor):

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
            config = self.generator._GenerateConfigFile__configure_device()
            self.assertEqual(config, expected_output)

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
            config = self.generator._GenerateConfigFile__configure_device()
            self.assertEqual(config, expected_output)

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
            config = self.generator._GenerateConfigFile__configure_device(invalid_config)

        # Confirm valid config received after second loop
        self.assertEqual(config, valid_config)

    def test_configure_device_prompt_config_key_handling(self):
        # Create mock config template with fake device type, 3 real params with
        # placeholder value (should trigger prompts), 1 param with value set
        # (should not prompt) and 1 invalid param (should not prompt)
        template = {
            "_type": "test-device",
            "nickname": "placeholder",
            "pin_data": "placeholder",
            "pin_clock": "placeholder",
            "default_rule": "50",
            "invalid_param": "placeholder"
        }

        # Expected config after values added to real params (invalid param
        # should still have placeholder)
        expected_output = {
            "_type": "test-device",
            "nickname": "nickname",
            "pin_data": "14",
            "pin_clock": "22",
            "default_rule": "50",
            "invalid_param": "placeholder"
        }

        # Mock prompt methods called for each key in config template
        # Mock schedule_rule_prompt (called regardless of config template)
        # Mock validate_rules to return True (would fail due to fake device type)
        with patch.object(self.generator, '_GenerateConfigFile__nickname_prompt') as mock_nickname_prompt, \
             patch.object(self.generator, '_GenerateConfigFile__pin_prompt') as mock_pin_prompt, \
             patch.object(self.generator, '_GenerateConfigFile__schedule_rule_prompt') as mock_schedule_prompt, \
             patch('config_generator.default_rule_prompt_router') as mock_default_rule_prompt, \
             patch('config_generator.validate_rules', return_value=True):

            # Mock user responses to each prompt
            mock_nickname_prompt.return_value = 'nickname'
            mock_pin_prompt.side_effect = ['14', '22']

            # Call configure_device method with mock config template
            self.generator._GenerateConfigFile__configure_device(template)

            # Confirm nickname prompt was called
            mock_nickname_prompt.assert_called_once()

            # Confirm pin prompt was called twice (pin_data and pin_clock)
            self.assertEqual(mock_pin_prompt.call_count, 2)
            self.assertEqual(
                mock_pin_prompt.call_args_list[0][0],
                (valid_device_pins, "Select data pin")
            )
            self.assertEqual(
                mock_pin_prompt.call_args_list[1][0],
                (valid_device_pins, "Select clock pin")
            )

            # Confirm default_rule prompt was NOT called (value already set)
            mock_default_rule_prompt.assert_not_called()

            # Confirm schedule rule prompt (receives finished config template)
            # was called with expected output
            mock_schedule_prompt.assert_called_once_with(expected_output)

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
            config = self.generator._GenerateConfigFile__configure_sensor()
            self.assertEqual(config, expected_output)

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
            config = self.generator._GenerateConfigFile__configure_sensor()
            self.assertEqual(config, expected_output)

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
            config = self.generator._GenerateConfigFile__configure_sensor()
            self.assertEqual(config, expected_output)

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
            config = self.generator._GenerateConfigFile__configure_sensor()
            self.assertEqual(config, expected_output)

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
            config = self.generator._GenerateConfigFile__configure_sensor()
            self.assertEqual(config, expected_output)

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
            config = self.generator._GenerateConfigFile__configure_sensor(invalid_config)

        # Confirm valid config received after second loop
        self.assertEqual(config, valid_config)

    def test_configure_sensor_prompt_config_key_handling(self):
        # Create mock config template with fake sensor type, 3 real params with
        # placeholder value (should trigger prompts), 1 param with value set
        # (should not prompt) and 1 invalid param (should not prompt)
        template = {
            "_type": "test-sensor",
            "nickname": "placeholder",
            "pin_data": "placeholder",
            "pin_clock": "placeholder",
            "default_rule": "50",
            "invalid_param": "placeholder"
        }

        # Expected config after values added to real params (invalid param
        # should still have placeholder)
        expected_output = {
            "_type": "test-sensor",
            "nickname": "nickname",
            "pin_data": "14",
            "pin_clock": "22",
            "default_rule": "50",
            "invalid_param": "placeholder"
        }

        # Mock prompt methods called for each key in config template
        # Mock schedule_rule_prompt (called regardless of config template)
        # Mock validate_rules to return True (would fail due to fake sensor type)
        with patch.object(self.generator, '_GenerateConfigFile__nickname_prompt') as mock_nickname_prompt, \
             patch.object(self.generator, '_GenerateConfigFile__pin_prompt') as mock_pin_prompt, \
             patch.object(self.generator, '_GenerateConfigFile__schedule_rule_prompt') as mock_schedule_prompt, \
             patch('config_generator.default_rule_prompt_router') as mock_default_rule_prompt, \
             patch('config_generator.validate_rules', return_value=True):

            # Mock user responses to each prompt
            mock_nickname_prompt.return_value = 'nickname'
            mock_pin_prompt.side_effect = ['14', '22']

            # Call configure_sensor method with mock config template
            self.generator._GenerateConfigFile__configure_sensor(template)

            # Confirm nickname prompt was called
            mock_nickname_prompt.assert_called_once()

            # Confirm pin prompt was called twice (pin_data and pin_clock)
            self.assertEqual(mock_pin_prompt.call_count, 2)
            self.assertEqual(
                mock_pin_prompt.call_args_list[0][0],
                (valid_sensor_pins, "Select data pin")
            )
            self.assertEqual(
                mock_pin_prompt.call_args_list[1][0],
                (valid_sensor_pins, "Select clock pin")
            )

            # Confirm default_rule prompt was NOT called (value already set)
            mock_default_rule_prompt.assert_not_called()

            # Confirm schedule rule prompt (receives finished config template)
            # was called with expected output
            mock_schedule_prompt.assert_called_once_with(expected_output)

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
        reset_config = self.generator._GenerateConfigFile__reset_config_template(invalid_config)

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

        # Confirm correct section added
        self.assertEqual(self.generator.config['ir_blaster'], expected_config)
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
        self.assertEqual(
            self.generator.config['sensor1']['targets'],
            ['device1', 'device2']
        )

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
            output = self.generator._GenerateConfigFile__add_schedule_rule(config)
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
            output = self.generator._GenerateConfigFile__add_schedule_rule(config)
            self.assertEqual(output['schedule'], {'10:00': 'Enabled'})

    def test_api_target_ip_prompt(self):
        # Simulate user selecting first option, confirm correct IP returned
        self.mock_ask.unsafe_ask.side_effect = ['node1']
        with patch('questionary.select', return_value=self.mock_ask):
            output = self.generator._GenerateConfigFile__apitarget_ip_prompt()
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
             patch.object(self.generator, '_GenerateConfigFile__apitarget_ip_prompt') as mock_ip_prompt:

            # Simulate user selecting first IP option
            mock_ip_prompt.return_value = '192.168.1.123'

            # Run prompt, confirm correct IP prompt is called
            self.generator._GenerateConfigFile__configure_device(config)
            self.assertTrue(mock_ip_prompt.called)

    def test_api_target_rule_prompt(self):
        # Mock nodes.json to include unit-test-config.json
        self.generator.existing_nodes = mock_cli_config['nodes']

        # Get absolute path to unit-test-config.json
        tests = os.path.dirname(os.path.realpath(__file__))
        cli = os.path.split(tests)[0]
        repo = os.path.dirname(cli)
        test_config = os.path.join(repo, 'util', 'unit-test-config.json')

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
             patch('config_rule_prompts.cli_config.get_config_filepath', return_value=test_config):

            rule = api_target_schedule_rule_prompt(mock_config)
            self.assertEqual(
                rule,
                {"on": ["enable", "device1"], "off": ["set_rule", "sensor1", "50"]}
            )

        # Call again with simulated input selecting IR Blaster options
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
             patch('config_rule_prompts.cli_config.get_config_filepath', return_value=test_config):

            rule = api_target_schedule_rule_prompt(mock_config)
            # Confirm correct rule returned
            self.assertEqual(rule, {"on": ["ir_key", "tv", "power"], "off": ["ignore"]})

        # Call schedule rule router with simulated input selecting 'Enabled' option
        self.mock_ask.unsafe_ask.side_effect = ['Enabled']
        with patch('questionary.select', return_value=self.mock_ask), \
             patch('questionary.text', return_value=self.mock_ask), \
             patch('questionary.confirm', return_value=self.mock_ask), \
             patch('config_rule_prompts.cli_config.get_config_filepath', return_value=test_config):

            rule = schedule_rule_prompt_router(mock_config)
            self.assertEqual(rule, 'Enabled')

        # Call default rule router with simulated input selecting ignore
        # option + endpoint requiring extra arg
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
             patch('config_rule_prompts.cli_config.get_config_filepath', return_value=test_config):

            rule = default_rule_prompt_router(mock_config)
            self.assertEqual(rule, {"on": ["ignore"], "off": ["enable_in", "sensor5", "1800"]})

    def test_api_call_prompt_target_config_missing(self):
        # Confirm script exits with error when unable to open config path
        with patch('builtins.open', side_effect=FileNotFoundError):
            with self.assertRaises(SystemExit):
                api_call_prompt({'ip': '192.168.1.234'})

        # Confirm script exits with error when IP not in nodes.json
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

        # Write to disk, confirm file exists
        self.generator.write_to_disk()
        path = os.path.join(
            mock_cli_config['config_directory'],
            'unit-test-existing-config.json'
        )
        self.assertTrue(os.path.exists(path))

        # Instantiate new generator with path to existing config
        generator = GenerateConfigFile(path)
        # Confirm edit_mode and config attributes
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
            self.assertEqual(
                mock_metadata_prompt.call_args_list[0][0],
                ("Unit Test Existing Config", "0", "Unit Test")
            )

            # Confirm passed_validation set to True (mock)
            self.assertTrue(generator.passed_validation)

        # Delete test config
        os.remove(path)

    def test_edit_invalid_config_path(self):
        # Create non-json config file
        with open('fake_config_file.txt', 'w', encoding='utf-8'):
            pass

        # Attempt to instantiate with non-json config file, confirm raises error
        with self.assertRaises(SystemExit):
            GenerateConfigFile('fake_config_file.txt')

        # Attempt to instantiate with non-existing config file, confirm raises error
        with self.assertRaises(SystemExit):
            GenerateConfigFile('/does/not/exist.json')

        # Delete fake config
        os.remove('fake_config_file.txt')


class TestCliUsage(TestCase):
    def test_call_with_no_arg(self):
        # Mock empty sys.argv (should show new config prompt)
        # Mock GenerateConfigFile class to confirm correct methods called
        with patch('sys.argv', ['./config_generator.py']), \
             patch(
                 'config_generator.GenerateConfigFile',
                 new=MagicMock(spec=GenerateConfigFile)
             ) as mock_class:  # noqa: E122

            # Simulate calling from command line
            main()

            # Confirm class was instantiated with no argument
            mock_class.assert_called_once_with()

            # Get instance created by main, confirm expected methods were called
            mock_instance = mock_class.return_value
            mock_instance.run_prompt.assert_called_once()
            mock_instance.write_to_disk.assert_called_once()

    def test_call_with_arg(self):
        # Mock sys.argv with path to config file (should show edit prompt)
        # Mock GenerateConfigFile class to confirm correct methods called
        with patch('sys.argv', ['./config_generator.py', 'config.json']), \
             patch(
                 'config_generator.GenerateConfigFile',
                 new=MagicMock(spec=GenerateConfigFile)
             ) as mock_class:  # noqa: E122

            # Simulate calling from command line
            main()

            # Confirm class was instantiated with config path arg
            mock_class.assert_called_once_with('config.json')

            # Get instance created by main, confirm expected methods were called
            mock_instance = mock_class.return_value
            mock_instance.run_prompt.assert_called_once()
            mock_instance.write_to_disk.assert_called_once()

    def test_failed_validation(self):
        # Mock empty sys.argv (should show new config prompt)
        # Mock GenerateConfigFile class to confirm correct methods called
        with patch('sys.argv', ['./config_generator.py']), \
             patch(
                 'config_generator.GenerateConfigFile',
                 new=MagicMock(spec=GenerateConfigFile)
             ) as mock_class:  # noqa: E122

            # Simulate user creating config that fails validation
            mock_class.return_value.passed_validation = False

            # Simulate calling from command line
            main()

            # Confirm class was instantiated with no argument
            mock_class.assert_called_once_with()

            # Get instance created by main, confirm expected methods were called
            mock_instance = mock_class.return_value
            mock_instance.run_prompt.assert_called_once()

            # Confirm did NOT write invalid config to disk
            mock_instance.write_to_disk.assert_not_called()
