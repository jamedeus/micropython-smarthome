import os
from unittest import TestCase
from unittest.mock import patch, MagicMock
from questionary import ValidationError
from config_generator import GenerateConfigFile, IntRange, FloatRange, MinLength, NicknameValidator

# Get paths to test dir, CLI dir, repo dir
tests = os.path.dirname(os.path.realpath(__file__))
cli = os.path.split(tests)[0]
repo = os.path.dirname(cli)
test_config = os.path.join(repo, 'frontend', 'node_configuration', 'unit-test-config.json')

# Mock nodes.json contents
mock_nodes = {
    "node1": {
        "config": test_config,
        "ip": "192.168.1.123"
    },
    "node2": {
        "config": '/not/a/real/directory',
        "ip": "192.168.1.223"
    }
}


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


class TestGenerateConfigFile(TestCase):
    def setUp(self):
        # Create instance with mocked keywords
        self.generator = GenerateConfigFile()
        self.generator.schedule_keyword_options = ['sunrise', 'sunset']

        # Mock replaces .ask() method to simulate user input
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
            'Timestamp',
            '10:00',
            'Int',
            '5',
            'Yes',
            'Timestamp',
            '20:00',
            'Int',
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
            'Timestamp',
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
            self.assertEqual(self.generator.used_nicknames, ['Motion', 'Thermostat', 'Sunrise'])
            self.assertEqual(self.generator.used_pins, ['14'])

        # Repeat test with thermostat
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
        self.mock_ask.ask.side_effect = [
            'DesktopTrigger',
            'Computer Activity',
            '192.168.1.123',
            'Enabled',
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
        self.mock_ask.ask.side_effect = [
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
        self.mock_ask.ask.side_effect = [
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
        self.generator.existing_nodes = mock_nodes

        # Simulate user selecting first option, confirm correct IP returned
        self.mock_ask.ask.side_effect = ['node1']
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
        self.mock_ask.ask.side_effect = ['No']
        with patch('questionary.select', return_value=self.mock_ask), \
             patch.object(self.generator, 'apitarget_ip_prompt') as mock_ip_prompt:

            # Simulate user selecting first IP option
            mock_ip_prompt.return_value = '192.168.1.123'

            # Run prompt, confirm correct IP prompt is called
            self.generator.configure_device(config)
            self.assertTrue(mock_ip_prompt.called)

    def test_api_target_rule_prompt(self):
        # Mock nodes.json to include unit-test-config.json
        self.generator.existing_nodes = mock_nodes

        # Simulate user at rule prompt after selecting IP matching unit-test-config.json
        mock_config = {
            "_type": "api-target",
            "nickname": "API",
            "ip": "192.168.1.123",
            "default_rule": "placeholder",
            "schedule": {}
        }

        # Call API target rule prompt with simulated user input, confirm correct rule returned
        self.mock_ask.ask.side_effect = [
            'API Call',
            True,
            'device1',
            'enable',
            True,
            'sensor1',
            'set_rule',
            'Int',
            '50'
        ]
        with patch('questionary.select', return_value=self.mock_ask), \
             patch('questionary.text', return_value=self.mock_ask), \
             patch('questionary.confirm', return_value=self.mock_ask):

            rule = self.generator.rule_prompt_with_api_call_prompt(mock_config)
            self.assertEqual(rule, {"on": ["enable", "device1"], "off": ["set_rule", "sensor1", "50"]})

        # Call again with simulated input selecting IR Blaster options, confirm correct rule returned
        self.mock_ask.ask.side_effect = [
            'API Call',
            True,
            'IR Blaster',
            'tv',
            'power',
            False,
        ]
        with patch('questionary.select', return_value=self.mock_ask), \
             patch('questionary.text', return_value=self.mock_ask), \
             patch('questionary.confirm', return_value=self.mock_ask):

            rule = self.generator.rule_prompt_with_api_call_prompt(mock_config)
            self.assertEqual(rule, {"on": ["ir_key", "tv", "power"], "off": ["ignore"]})

        # Call schedule rule router with simulated input selecting 'Enabled' option
        self.mock_ask.ask.side_effect = ['Enabled']
        with patch('questionary.select', return_value=self.mock_ask), \
             patch('questionary.text', return_value=self.mock_ask), \
             patch('questionary.confirm', return_value=self.mock_ask):

            rule = self.generator.schedule_rule_prompt_router(mock_config)
            self.assertEqual(rule, 'Enabled')

        # Call default rule router with simulated input selecting ignore option + endpoint requiring extra arg
        self.mock_ask.ask.side_effect = [
            False,
            True,
            'sensor5',
            'enable_in',
            '1800'
        ]
        with patch('questionary.select', return_value=self.mock_ask), \
             patch('questionary.text', return_value=self.mock_ask), \
             patch('questionary.confirm', return_value=self.mock_ask):

            rule = self.generator.default_rule_prompt_router(mock_config)
            self.assertEqual(rule, {"on": ["ignore"], "off": ["enable_in", "sensor5", "1800"]})

    def test_api_call_prompt_target_config_missing(self):
        # Mock nodes.json to include node with fake config path
        self.generator.existing_nodes = mock_nodes

        # Confirm script exits with error when unable to open fake path
        with self.assertRaises(SystemExit):
            self.generator.api_call_prompt({'ip': '192.168.1.223'})

        # Confirm script exits with error when IP not in nodes.json
        with self.assertRaises(SystemExit):
            self.generator.api_call_prompt({'ip': '10.0.0.1'})


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
            'Timestamp',
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
