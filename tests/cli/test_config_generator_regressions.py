import os
from unittest import TestCase
from unittest.mock import patch, MagicMock
from config_generator import GenerateConfigFile
from config_rule_prompts import (
    default_rule_prompt_router,
    schedule_rule_prompt_router,
)
from mock_cli_config import mock_cli_config


class TestRegressions(TestCase):
    def setUp(self):
        # Create instance with mocked keywords
        self.generator = GenerateConfigFile()
        self.generator.schedule_keyword_options = ['sunrise', 'sunset']

        # Mock replaces .ask() method to simulate user input
        self.mock_ask = MagicMock()

        # Path to mock existing config file (created in tests)
        self.existing_config_path = os.path.join(
            mock_cli_config['config_directory'],
            'unit-test-existing-config.json'
        )

    @classmethod
    def tearDownClass(cls):
        # Delete unit-test-existing-config.json from disk if it still exists
        existing_config_path = os.path.join(
            mock_cli_config['config_directory'],
            'unit-test-existing-config.json'
        )
        if os.path.exists(existing_config_path):
            os.remove(existing_config_path)

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
            self.generator.config['sensor1'] = self.generator._GenerateConfigFile__configure_sensor()
            self.assertEqual(self.generator.config['sensor1'], sensor_config)

        # Simulate user attempting to add a duplicate SI7021
        self.mock_ask.unsafe_ask.side_effect = ['SI7021 Temperature Sensor']
        with patch('questionary.select', return_value=self.mock_ask) as mock_select:
            # Run sensor type select prompt
            self.generator._GenerateConfigFile__sensor_type()

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

        # Write to disk, confirm file exists
        self.generator.write_to_disk()
        self.assertTrue(os.path.exists(self.existing_config_path))

        # Instantiate new generator with path to existing config (simulate editing)
        generator = GenerateConfigFile(self.existing_config_path)
        # Confirm edit_mode and config attributes
        self.assertTrue(generator.edit_mode)
        self.assertEqual(generator.config, self.generator.config)

        # Simulate user attempting to add a duplicate SI7021
        self.mock_ask.unsafe_ask.side_effect = ['SI7021 Temperature Sensor']
        with patch('questionary.select', return_value=self.mock_ask) as mock_select:
            # Run sensor type select prompt
            generator._GenerateConfigFile__sensor_type()

            # Confirm SI7021 was NOT in options list
            _, kwargs = mock_select.call_args
            self.assertFalse('SI7021 Temperature Sensor' in kwargs['choices'])

        # Delete test config
        os.remove(self.existing_config_path)

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

        # Write to disk, confirm file exists
        self.generator.write_to_disk()
        self.assertTrue(os.path.exists(self.existing_config_path))

        # Instantiate new generator with path to existing config, confirm edit_mode and config attributes
        generator = GenerateConfigFile(self.existing_config_path)
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
            generator.config['sensor1'] = generator._GenerateConfigFile__configure_sensor()

            # Confirm SI7021 option appeared (config no longer contains si7021)
            _, kwargs = mock_select.call_args
            self.assertFalse('SI7021 Temperature Sensor' in kwargs['choices'])

        # Delete test config
        os.remove(self.existing_config_path)

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

    # Original bug: When devices and sensors were deleted the selected keys
    # were deleted from config dict without adjusting index to prevent gaps.
    # However, when devices/sensors are added the index is determined by the
    # number of existing devices/sensors, not the highest index. This could
    # result in a new device/sensor overwriting one that wasn't deleted.
    def test_prevent_non_sequential_device_and_sensor_indices(self):
        # Start with multiple devices and sensors
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
                "nickname": "Sensor1",
                "pin": "5",
                "default_rule": "5",
                "schedule": {},
                "targets": []
            },
            "sensor2": {
                "_type": "pir",
                "nickname": "Sensor2",
                "pin": "21",
                "default_rule": "5",
                "schedule": {},
                "targets": []
            }
        }

        # Confirm initial config keys
        self.assertEqual(
            list(self.generator.config.keys()),
            ["metadata", "device1", "device2", "sensor1", "sensor2"]
        )

        # Mock user deleting device1 and sensor1, run prompt
        self.mock_ask.unsafe_ask.return_value = [
            "Target1 (mosfet)",
            "Sensor1 (pir)"
        ]
        with patch("questionary.checkbox", return_value=self.mock_ask):
            self.generator.delete_devices_and_sensors()
            self.assertTrue(self.mock_ask.called_once)

        # Confirm device1 and sensor1 were deleted, device2 and sensor2 IDs
        # were decremented to keep index sequential
        self.assertEqual(
            list(self.generator.config.keys()),
            ["metadata", "device1", "sensor1"]
        )
        self.assertEqual(self.generator.config["device1"]["nickname"], "Target2")
        self.assertEqual(self.generator.config["sensor1"]["nickname"], "Sensor2")
