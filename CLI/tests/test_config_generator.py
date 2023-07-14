from unittest import TestCase
from unittest.mock import patch, MagicMock
from questionary import ValidationError
from config_generator import GenerateConfigFile, IntRange, FloatRange


# Simulate user input object passed to validators
class SimulatedInput:
    def __init__(self, text):
        self.text = text


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


class TestGenerateConfigFile(TestCase):
    def setUp(self):
        self.generator = GenerateConfigFile()

        self.mock_ask = MagicMock()

    def test_run_prompt_method(self):
        # Mock all methods called by run_prompt
        with patch.object(self.generator, 'metadata_prompt') as mock_metadata_prompt, \
             patch.object(self.generator, 'wifi_prompt') as mock_wifi_prompt, \
             patch.object(self.generator, 'add_devices_and_sensors') as mock_add_devices_and_sensors, \
             patch.object(self.generator, 'select_sensor_targets') as mock_select_sensor_targets:

            # Run method, confirm all mocks called
            self.generator.run_prompt()
            self.assertTrue(mock_metadata_prompt.called_once)
            self.assertTrue(mock_wifi_prompt.called_once)
            self.assertTrue(mock_add_devices_and_sensors.called_once)
            self.assertTrue(mock_select_sensor_targets.called_once)

    def test_metadata_prompt(self):
        # Mock responses to the ID, Floor, and Location prompts
        self.mock_ask.ask.side_effect = ['Test ID', '2', 'Test Environment']
        with patch('questionary.text', return_value=self.mock_ask):
            self.generator.metadata_prompt()

        # Confirm responses added to correct keys in dict
        self.assertEqual(self.generator.config['metadata']['id'], 'Test ID')
        self.assertEqual(self.generator.config['metadata']['floor'], '2')
        self.assertEqual(self.generator.config['metadata']['location'], 'Test Environment')

    def test_wifi_prompt(self):
        # Mock responses to the SSID and Password prompts
        self.mock_ask.ask.side_effect = ['MyNetwork', 'hunter2']
        with patch('questionary.text', return_value=self.mock_ask), \
             patch('questionary.password', return_value=self.mock_ask):
            self.generator.wifi_prompt()

        # Confirm responses added to correct keys in dict
        self.assertEqual(self.generator.config['wifi']['ssid'], 'MyNetwork')
        self.assertEqual(self.generator.config['wifi']['password'], 'hunter2')

    def test_sensor_type(self):
        self.mock_ask.ask.return_value = 'MotionSensor'

        with patch('questionary.select', return_value=self.mock_ask):
            self.assertEqual(self.generator.sensor_type(), 'MotionSensor')

    def test_device_type(self):
        self.mock_ask.ask.return_value = 'Dimmer'

        with patch('questionary.select', return_value=self.mock_ask):
            self.assertEqual(self.generator.device_type(), 'Dimmer')

    def test_unique_nickname(self):
        # Add an already-used nickname
        self.generator.used_nicknames = ['Used']

        # Should reject already-used nickname, accept all others
        self.assertFalse(self.generator.unique_nickname('Used'))
        self.assertTrue(self.generator.unique_nickname('Unused'))

    def test_nickname_prompt(self):
        # Add an already-used nickname
        self.generator.used_nicknames = ['Used']

        # Mock ask to return a different nickname
        self.mock_ask.ask.return_value = 'Unused'
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
            "min_bright": "1",
            "max_bright": "100",
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
        self.mock_ask.ask.side_effect = [
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

    def test_configure_device_prompt(self):
        expected_output = {
            "_type": "dimmer",
            "nickname": "Overhead Lights",
            "ip": "192.168.1.123",
            "min_bright": "1",
            "max_bright": "100",
            "default_rule": "50",
            "schedule": {
                "10:00": "100",
                "20:00": "fade/25/3600",
                "00:00": "Disabled"
            }
        }

        # Mock ask to return parameters in expected order
        self.mock_ask.ask.side_effect = [
            'Dimmer',
            'Overhead Lights',
            '192.168.1.123',
            '1',
            '100',
            '50',
            'Yes',
            '10:00',
            'Int',
            '100',
            'Yes',
            '20:00',
            'Fade',
            '25',
            '3600',
            'Yes',
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
        self.mock_ask.ask.side_effect = [
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
        # Invalid config object with default_rule greater than max_bright
        invalid_config = {
            "_type": "dimmer",
            "nickname": "Overhead Lights",
            "ip": "192.168.1.123",
            "min_bright": "1",
            "max_bright": "50",
            "default_rule": "100",
            "schedule": {}
        }

        # Valid config expected after test complete
        valid_config = {
            '_type': 'dimmer',
            'nickname': 'Overhead Lights',
            'ip': '192.168.1.123',
            'min_bright': '1',
            'max_bright': '100',
            'default_rule': '50',
            'schedule': {}
        }

        # Mock ask to return user input in expected order
        self.mock_ask.ask.side_effect = [
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
        self.mock_ask.ask.side_effect = [
            'MotionSensor',
            'Motion',
            '14',
            '5',
            'Yes',
            '10:00',
            'Int',
            '5',
            'Yes',
            '20:00',
            'Int',
            '1',
            'Yes',
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
            "schedule": {
                "10:00": "75"
            },
            "targets": []
        }

        # Mock ask to return parameters in expected order
        self.mock_ask.ask.side_effect = [
            'Thermostat',
            'Thermostat',
            '70',
            'cool',
            '1.5',
            'Yes',
            '10:00',
            'Int',
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

        # Repeat test with thermostat
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
        self.mock_ask.ask.side_effect = [
            'Dummy',
            'Sunrise',
            'On',
            'Yes',
            '06:00',
            'On',
            'Yes',
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
            self.assertEqual(self.generator.used_nicknames, ['Motion', 'Thermostat', 'Sunrise'])
            self.assertEqual(self.generator.used_pins, ['14'])

        # Repeat test with thermostat
        expected_output = {
            "_type": "desktop",
            "nickname": "Computer Activity",
            "ip": "192.168.1.123",
            "default_rule": "Enabled",
            "schedule": {
                "10:00": "Enabled"
            },
            "targets": []
        }

        # Mock ask to return parameters in expected order
        self.mock_ask.ask.side_effect = [
            'DesktopTrigger',
            'Computer Activity',
            '192.168.1.123',
            'Enabled',
            'Yes',
            '10:00',
            'Enabled',
            'No'
        ]
        with patch('questionary.select', return_value=self.mock_ask), \
             patch('questionary.text', return_value=self.mock_ask):

            # Run prompt, confirm output matches expected
            config = self.generator.configure_sensor()
            self.assertEqual(config, expected_output)

            # Confirm nickname and pin added to used lists
            self.assertEqual(self.generator.used_nicknames, ['Motion', 'Thermostat', 'Sunrise', 'Computer Activity'])
            self.assertEqual(self.generator.used_pins, ['14'])

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
        self.mock_ask.ask.side_effect = [
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
            ]
        }

        # Mock user input
        self.mock_ask.ask.side_effect = [
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
            "wifi": {
                "ssid": "mynet",
                "password": "hunter2"
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
        self.mock_ask.ask.return_value = ['Target1 (mosfet)', 'Target2 (mosfet)']
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
            "wifi": {
                "ssid": "mynet",
                "password": "hunter2"
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


class TestRegressions(TestCase):
    def setUp(self):
        self.generator = GenerateConfigFile()

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
            "schedule": {
                "10:00": "75"
            },
            "targets": []
        }

        # Mock ask to return parameters in expected order
        self.mock_ask.ask.side_effect = [
            'Thermostat',
            'Thermostat',
            '70',
            'cool',
            '1.5',
            'Yes',
            '10:00',
            'Int',
            '75',
            'No'
        ]
        with patch('questionary.select', return_value=self.mock_ask), \
             patch('questionary.text', return_value=self.mock_ask):

            # Run prompt, confirm output matches expected
            config = self.generator.configure_sensor()
            self.assertEqual(config, sensor_config)

        # Confirm Thermostat option removed from sensor type options
        self.assertNotIn('Thermostat', self.generator.sensor_type_options)
