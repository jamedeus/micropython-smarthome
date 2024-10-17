'''Unit tests for the interactive menu shown when api_client.py is called from
the command line with no arguments.
'''

# pylint: disable=missing-function-docstring, missing-class-docstring, missing-class-docstring

from unittest import TestCase
from unittest.mock import patch, MagicMock
from test_api_client import mock_status_object
from api_client import (
    api_prompt,
    main,
    get_endpoint_options,
    device_or_sensor_rule_prompt
)

mock_config = {
    "metadata": {
        "id": "Test1",
        "floor": "1",
        "location": "Inside cabinet above microwave",
        "schedule_keywords": {
            "morning": "08:30",
            "sleep": "22:30",
            "sunrise": "06:00",
            "sunset": "18:00",
            "relax": "20:30"
        }
    },
    "sensor1": {
        "_type": "pir",
        "nickname": "Motion Sensor",
        "default_rule": "2.0",
        "pin": "5",
        "schedule": {
            "10:00": "2",
            "22:00": "2"
        },
        "targets": [
            "device1",
            "device2"
        ]
    },
    "device1": {
        "_type": "pwm",
        "nickname": "Cabinet Lights",
        "min_rule": "0",
        "max_rule": "1023",
        "default_rule": "1023",
        "pin": "13",
        "schedule": {
            "00:00": "fade/32/7200",
            "05:00": "Disabled",
            "22:01": "fade/256/7140",
            "22:00": "1023"
        }
    },
    "device2": {
        "_type": "tasmota-relay",
        "nickname": "Overhead Lights",
        "ip": "192.168.1.203",
        "default_rule": "Enabled",
        "schedule": {
            "05:00": "Enabled",
            "22:00": "Disabled"
        }
    }
}

mock_ir_config = {
    "metadata": {
        "id": "Mock IR Config",
        "floor": "1",
        "location": "Behind TV",
        "schedule_keywords": {
            "morning": "08:30",
            "sleep": "22:30",
            "sunrise": "06:00",
            "sunset": "18:00",
            "relax": "20:30"
        }
    },
    "ir_blaster": {
        "pin": "4",
        "target": [
            "samsung_tv",
            "whynter_ac"
        ],
        "macros": {
            "start_ac": [
                ("whynter_ac", "on", "100", "1"),
                ("whynter_ac", "start", "0", "1")
            ]
        }
    }
}

mock_ir_status = {
    'metadata': {
        'id': 'Mock IR Config',
        'floor': '1',
        'location': 'Behind TV',
        'ir_blaster': True,
        'ir_targets': [
            'samsung_tv',
            'whynter_ac'
        ],
        "schedule_keywords": {
            "sunrise": "06:00",
            "sunset": "18:00",
            "sleep": "23:00"
        }
    },
    'devices': {},
    'sensors': {}
}


class InteractiveMenuTests(TestCase):
    def setUp(self):
        # Mock replaces .unsafe_ask() method to simulate user input
        # Each test sets side_effect with list of simulated user inputs
        self.mock_ask = MagicMock()

        # Mock questionary prompts to return the next item in mock_ask lists
        patch('questionary.select', return_value=self.mock_ask).start()
        patch('questionary.text', return_value=self.mock_ask).start()

        # Mock questionary press any key to continue
        patch('questionary.press_any_key_to_continue').start()

        # Mock config file read from disk in tests
        # Note: This effects CliConfigManager singleton (shared between tests)
        self.mock_load = patch(
            'api_client.cli_config.load_node_config_file',
            return_value=mock_config
        )
        self.mock_load.start()

    def tearDown(self):
        # Reset mock to prevent breaking tests in other files
        self.mock_load.stop()

    def test_runs_interactive_prompt_when_called_with_no_args(self):
        # Mock empty sys.argv (should run interactive prompt)
        with patch('sys.argv', ['api_client.py']), \
             patch('api_client.api_prompt') as mock_interactive_prompt:

            # Call main, confirm interactive prompt started
            main()
            mock_interactive_prompt.assert_called()

        # Mock sys.argv with --no-sync flag (should handle the same as empty)
        with patch('sys.argv', ['api_client.py', '--no-sync']), \
             patch('api_client.api_prompt') as mock_interactive_prompt:

            # Call main, confirm interactive prompt started
            main()
            mock_interactive_prompt.assert_called()

    def test_enter_node_ip_address(self):
        # Simulate user selecting "Enter node IP" instead of node name, typing
        # IP address, then selecting clear_log endpoint
        self.mock_ask.unsafe_ask.side_effect = [
            'Enter node IP',
            '192.168.1.101',
            'clear_log',
            'Done',
            'Done'
        ]

        # Mock parse_command to return status, then API response from ESP32,
        # then status again (prompt restarts)
        with patch('api_client.parse_command', side_effect=[
            mock_status_object,
            {'clear_log': 'success'},
            mock_status_object
        ]) as mock_parse_command:

            # Run prompt, will complete immediately with mock input
            api_prompt()

            # Confirm called parse_command 3 times
            self.assertEqual(mock_parse_command.call_count, 3)

            # First call: requested status object from target node
            self.assertEqual(
                mock_parse_command.call_args_list[0][0],
                ("192.168.1.101", ["status"])
            )

            # Second call: sent clear_log command
            self.assertEqual(
                mock_parse_command.call_args_list[1][0],
                ("192.168.1.101", ["clear_log"])
            )

            # Third call: requested updated status object after API call
            self.assertEqual(
                mock_parse_command.call_args_list[2][0],
                ("192.168.1.101", ["status"])
            )

    def test_enable_endpoint(self):
        # Simulate user selecting node1, enable, sensor1
        self.mock_ask.unsafe_ask.side_effect = [
            'node1',
            'enable',
            'sensor1',
            'Done',
            'Done'
        ]

        # Mock parse_command to return status, then API response from ESP32,
        # then status again (prompt restarts)
        with patch('api_client.parse_command', side_effect=[
            mock_status_object,
            {'Enabled': 'sensor1'},
            mock_status_object
        ]) as mock_parse_command:

            # Run prompt, will complete immediately with mock input
            api_prompt()

            # Confirm called parse_command 3 times
            self.assertEqual(mock_parse_command.call_count, 3)

            # First call: requested status object from target node
            self.assertEqual(
                mock_parse_command.call_args_list[0][0],
                ("192.168.1.123", ["status"])
            )

            # Second call: sent enable command with correct arg
            self.assertEqual(
                mock_parse_command.call_args_list[1][0],
                ("192.168.1.123", ["enable", "sensor1"])
            )

            # Third call: requested updated status object after API call
            self.assertEqual(
                mock_parse_command.call_args_list[2][0],
                ("192.168.1.123", ["status"])
            )

    def test_enable_in_endpoint(self):
        # Simulate user selecting node1, enable_in, sensor1, 5
        self.mock_ask.unsafe_ask.side_effect = [
            'node1',
            'enable_in',
            'sensor1',
            '5',
            'Done',
            'Done'
        ]

        # Mock parse_command to return status, then API response from ESP32,
        # then status again (prompt restarts)
        with patch('api_client.parse_command', side_effect=[
            mock_status_object,
            {'Enabled': 'sensor1', 'Enable_in_seconds': 300.0},
            mock_status_object
        ]) as mock_parse_command:

            # Run prompt, will complete immediately with mock input
            api_prompt()

            # Confirm called parse_command 3 times
            self.assertEqual(mock_parse_command.call_count, 3)

            # First call: requested status object from target node
            self.assertEqual(
                mock_parse_command.call_args_list[0][0],
                ("192.168.1.123", ["status"])
            )

            # Second call: sent enable command with correct arg
            self.assertEqual(
                mock_parse_command.call_args_list[1][0],
                ("192.168.1.123", ["enable_in", "sensor1", "5"])
            )

            # Third call: requested updated status object after API call
            self.assertEqual(
                mock_parse_command.call_args_list[2][0],
                ("192.168.1.123", ["status"])
            )

    def test_set_rule_endpoint(self):
        # Simulate user selecting node1, set_rule, sensor1, 5
        self.mock_ask.unsafe_ask.side_effect = [
            'node1',
            'set_rule',
            'sensor1',
            '5',
            'Done',
            'Done'
        ]

        # Mock parse_command to return status, then API response from ESP32,
        # then status again (prompt restarts)
        with patch('api_client.parse_command', side_effect=[
            mock_status_object,
            {'sensor1': '5'},
            mock_status_object
        ]) as mock_parse_command:

            # Run prompt, will complete immediately with mock input
            api_prompt()

            # Confirm called parse_command 3 times
            self.assertEqual(mock_parse_command.call_count, 3)

            # First call: requested status object from target node
            self.assertEqual(
                mock_parse_command.call_args_list[0][0],
                ("192.168.1.123", ["status"])
            )

            # Second call: sent enable command with correct arg
            self.assertEqual(
                mock_parse_command.call_args_list[1][0],
                ("192.168.1.123", ["set_rule", "sensor1", "5"])
            )

            # Third call: requested updated status object after API call
            self.assertEqual(
                mock_parse_command.call_args_list[2][0],
                ("192.168.1.123", ["status"])
            )

    def test_increment_rule_endpoint(self):
        # Simulate user selecting node1, increment_rule, sensor1, 5
        self.mock_ask.unsafe_ask.side_effect = [
            'node1',
            'increment_rule',
            'sensor1',
            '5',
            'Done',
            'Done'
        ]

        # Mock parse_command to return status, then API response from ESP32,
        # then status again (prompt restarts)
        with patch('api_client.parse_command', side_effect=[
            mock_status_object,
            {'sensor1': '6'},
            mock_status_object
        ]) as mock_parse_command:

            # Run prompt, will complete immediately with mock input
            api_prompt()

            # Confirm called parse_command 3 times
            self.assertEqual(mock_parse_command.call_count, 3)

            # First call: requested status object from target node
            self.assertEqual(
                mock_parse_command.call_args_list[0][0],
                ("192.168.1.123", ["status"])
            )

            # Second call: sent enable command with correct arg
            self.assertEqual(
                mock_parse_command.call_args_list[1][0],
                ("192.168.1.123", ["increment_rule", "sensor1", "5"])
            )

            # Third call: requested updated status object after API call
            self.assertEqual(
                mock_parse_command.call_args_list[2][0],
                ("192.168.1.123", ["status"])
            )

    def test_add_rule_endpoint(self):
        # Simulate user selecting node1, add_rule, sensor1, Timestamp, 12:00, 5
        self.mock_ask.unsafe_ask.side_effect = [
            'node1',
            'add_rule',
            'sensor1',
            'Timestamp',
            '12:00',
            '5',
            'Done',
            'Done'
        ]

        # Mock parse_command to return status, then API response from ESP32,
        # then status again (prompt restarts)
        with patch('api_client.parse_command', side_effect=[
            mock_status_object,
            {'time': '12:00', 'Rule added': 5},
            mock_status_object
        ]) as mock_parse_command:

            # Run prompt, will complete immediately with mock input
            api_prompt()

            # Confirm called parse_command 3 times
            self.assertEqual(mock_parse_command.call_count, 3)

            # First call: requested status object from target node
            self.assertEqual(
                mock_parse_command.call_args_list[0][0],
                ("192.168.1.123", ["status"])
            )

            # Second call: sent enable command with correct arg
            self.assertEqual(
                mock_parse_command.call_args_list[1][0],
                ("192.168.1.123", ["add_rule", "sensor1", "12:00", "5"])
            )

            # Third call: requested updated status object after API call
            self.assertEqual(
                mock_parse_command.call_args_list[2][0],
                ("192.168.1.123", ["status"])
            )

    def test_remove_rule_endpoint(self):
        # Simulate user selecting node1, remove_rule, sensor1, 10:00
        self.mock_ask.unsafe_ask.side_effect = [
            'node1',
            'remove_rule',
            'sensor1',
            '10:00',
            'Done',
            'Done'
        ]

        # Mock parse_command to return status, then API response from ESP32,
        # then status again (prompt restarts)
        with patch('api_client.parse_command', side_effect=[
            mock_status_object,
            {'Deleted': '10:00'},
            mock_status_object
        ]) as mock_parse_command:

            # Run prompt, will complete immediately with mock input
            api_prompt()

            # Confirm called parse_command 3 times
            self.assertEqual(mock_parse_command.call_count, 3)

            # First call: requested status object from target node
            self.assertEqual(
                mock_parse_command.call_args_list[0][0],
                ("192.168.1.123", ["status"])
            )

            # Second call: sent enable command with correct arg
            self.assertEqual(
                mock_parse_command.call_args_list[1][0],
                ("192.168.1.123", ["remove_rule", "sensor1", "10:00"])
            )

            # Third call: requested updated status object after API call
            self.assertEqual(
                mock_parse_command.call_args_list[2][0],
                ("192.168.1.123", ["status"])
            )

    def test_reboot_endpoint(self):
        # Simulate user selecting node1, reboot
        # Only need to select Done once (loop exits after reboot command)
        self.mock_ask.unsafe_ask.side_effect = [
            'node1',
            'reboot',
            'Done'
        ]

        # Mock parse_command to return status, then API response from ESP32
        with patch('api_client.parse_command', side_effect=[
            mock_status_object,
            'Rebooting'
        ]) as mock_parse_command:

            # Run prompt, will complete immediately with mock input
            api_prompt()

            # Confirm called parse_command 2 times
            self.assertEqual(mock_parse_command.call_count, 2)

            # First call: requested status object from target node
            self.assertEqual(
                mock_parse_command.call_args_list[0][0],
                ("192.168.1.123", ["status"])
            )

            # Second call: sent reboot command
            self.assertEqual(
                mock_parse_command.call_args_list[1][0],
                ("192.168.1.123", ["reboot"])
            )

    def test_turn_on_endpoint(self):
        # Simulate user selecting node1, turn_on, device1
        self.mock_ask.unsafe_ask.side_effect = [
            'node1',
            'turn_on',
            'device1',
            'Done',
            'Done'
        ]

        # Mock parse_command to return status, then API response from ESP32,
        # then status again (prompt restarts)
        with patch('api_client.parse_command', side_effect=[
            mock_status_object,
            {'On': 'device1'},
            mock_status_object
        ]) as mock_parse_command:

            # Run prompt, will complete immediately with mock input
            api_prompt()

            # Confirm called parse_command 3 times
            self.assertEqual(mock_parse_command.call_count, 3)

            # First call: requested status object from target node
            self.assertEqual(
                mock_parse_command.call_args_list[0][0],
                ("192.168.1.123", ["status"])
            )

            # Second call: sent turn_on command with correct arg
            self.assertEqual(
                mock_parse_command.call_args_list[1][0],
                ("192.168.1.123", ["turn_on", "device1"])
            )

            # Third call: requested updated status object after API call
            self.assertEqual(
                mock_parse_command.call_args_list[2][0],
                ("192.168.1.123", ["status"])
            )

    def test_trigger_sensor_endpoint(self):
        # Simulate user selecting node1, trigger_sensor, sensor1
        self.mock_ask.unsafe_ask.side_effect = [
            'node1',
            'trigger_sensor',
            'sensor1',
            'Done',
            'Done'
        ]

        # Mock parse_command to return status, then API response from ESP32,
        # then status again (prompt restarts)
        with patch('api_client.parse_command', side_effect=[
            mock_status_object,
            {'Triggered': 'sensor1'},
            mock_status_object
        ]) as mock_parse_command:

            # Run prompt, will complete immediately with mock input
            api_prompt()

            # Confirm called parse_command 3 times
            self.assertEqual(mock_parse_command.call_count, 3)

            # First call: requested status object from target node
            self.assertEqual(
                mock_parse_command.call_args_list[0][0],
                ("192.168.1.123", ["status"])
            )

            # Second call: sent trigger_sensor command with correct arg
            self.assertEqual(
                mock_parse_command.call_args_list[1][0],
                ("192.168.1.123", ["trigger_sensor", "sensor1"])
            )

            # Third call: requested updated status object after API call
            self.assertEqual(
                mock_parse_command.call_args_list[2][0],
                ("192.168.1.123", ["status"])
            )

    def test_add_schedule_keyword_endpoint(self):
        # Simulate user selecting node1, add_schedule_keyword, then type Lunch, 12:00
        self.mock_ask.unsafe_ask.side_effect = [
            'node1',
            'add_schedule_keyword',
            'Lunch',
            '12:00',
            'Done',
            'Done'
        ]

        # Mock parse_command to return status, then API response from ESP32,
        # then status again (prompt restarts)
        with patch('api_client.parse_command', side_effect=[
            mock_status_object,
            {'Keyword added': 'Lunch', 'time': '12:00'},
            mock_status_object
        ]) as mock_parse_command:

            # Run prompt, will complete immediately with mock input
            api_prompt()

            # Confirm called parse_command 3 times
            self.assertEqual(mock_parse_command.call_count, 3)

            # First call: requested status object from target node
            self.assertEqual(
                mock_parse_command.call_args_list[0][0],
                ("192.168.1.123", ["status"])
            )

            # Second call: sent enable command with correct arg
            self.assertEqual(
                mock_parse_command.call_args_list[1][0],
                ("192.168.1.123", ["add_schedule_keyword", "Lunch", "12:00"])
            )

            # Third call: requested updated status object after API call
            self.assertEqual(
                mock_parse_command.call_args_list[2][0],
                ("192.168.1.123", ["status"])
            )

    def test_remove_schedule_keyword_endpoint(self):
        # Simulate user selecting node1, remove_schedule_keyword, sleep
        self.mock_ask.unsafe_ask.side_effect = [
            'node1',
            'remove_schedule_keyword',
            'sleep',
            'Done',
            'Done'
        ]

        # Mock parse_command to return status, then API response from ESP32,
        # then status again (prompt restarts)
        with patch('api_client.parse_command', side_effect=[
            mock_status_object,
            {'Keyword removed': 'sleep'},
            mock_status_object
        ]) as mock_parse_command:

            # Run prompt, will complete immediately with mock input
            api_prompt()

            # Confirm called parse_command 3 times
            self.assertEqual(mock_parse_command.call_count, 3)

            # First call: requested status object from target node
            self.assertEqual(
                mock_parse_command.call_args_list[0][0],
                ("192.168.1.123", ["status"])
            )

            # Second call: sent enable command with correct arg
            self.assertEqual(
                mock_parse_command.call_args_list[1][0],
                ("192.168.1.123", ["remove_schedule_keyword", "sleep"])
            )

            # Third call: requested updated status object after API call
            self.assertEqual(
                mock_parse_command.call_args_list[2][0],
                ("192.168.1.123", ["status"])
            )

    def test_set_gps_coords_endpoint(self):
        # Simulate user selecting node1, set_gps_coords, then type -77.8, 166.6
        self.mock_ask.unsafe_ask.side_effect = [
            'node1',
            'set_gps_coords',
            '-77.8',
            '166.6',
            'Done',
            'Done'
        ]

        # Mock parse_command to return status, then API response from ESP32,
        # then status again (prompt restarts)
        with patch('api_client.parse_command', side_effect=[
            mock_status_object,
            {'Success': 'GPS coordinates set"'},
            mock_status_object
        ]) as mock_parse_command:

            # Run prompt, will complete immediately with mock input
            api_prompt()

            # Confirm called parse_command 3 times
            self.assertEqual(mock_parse_command.call_count, 3)

            # First call: requested status object from target node
            self.assertEqual(
                mock_parse_command.call_args_list[0][0],
                ("192.168.1.123", ["status"])
            )

            # Second call: sent enable command with correct arg
            self.assertEqual(
                mock_parse_command.call_args_list[1][0],
                ("192.168.1.123", ["set_gps_coords", "-77.8", "166.6"])
            )

            # Third call: requested updated status object after API call
            self.assertEqual(
                mock_parse_command.call_args_list[2][0],
                ("192.168.1.123", ["status"])
            )

    def test_set_log_level_endpoint(self):
        # Simulate user selecting node1, set_log_level, DEBUG
        self.mock_ask.unsafe_ask.side_effect = [
            'node1',
            'set_log_level',
            'DEBUG',
            'Done',
            'Done'
        ]

        # Mock parse_command to return status, then API response from ESP32,
        # then status again (prompt restarts)
        with patch('api_client.parse_command', side_effect=[
            mock_status_object,
            {"Success": "Log level set (takes effect after reboot)"},
            mock_status_object
        ]) as mock_parse_command:

            # Run prompt, will complete immediately with mock input
            api_prompt()

            # Confirm called parse_command 3 times
            self.assertEqual(mock_parse_command.call_count, 3)

            # First call: requested status object from target node
            self.assertEqual(
                mock_parse_command.call_args_list[0][0],
                ("192.168.1.123", ["status"])
            )

            # Second call: sent set_log_level command with correct arg
            self.assertEqual(
                mock_parse_command.call_args_list[1][0],
                ("192.168.1.123", ["set_log_level", "DEBUG"])
            )

            # Third call: requested updated status object after API call
            self.assertEqual(
                mock_parse_command.call_args_list[2][0],
                ("192.168.1.123", ["status"])
            )

    def test_exit_without_selecting_node(self):
        # Simulate user selecting "Done" at node select prompt
        self.mock_ask.unsafe_ask.side_effect = ['Done']
        with patch('api_client.parse_command') as mock_parse_command:
            # Run prompt, will complete immediately with mock input
            api_prompt()

            # Confirm parse_command was not called
            self.assertEqual(mock_parse_command.call_count, 0)


class InteractiveIrBlasterMenuTests(TestCase):
    def setUp(self):
        # Mock replaces .unsafe_ask() method to simulate user input
        # Each test sets side_effect with list of simulated user inputs
        self.mock_ask = MagicMock()

        # Mock questionary prompts to return the next item in mock_ask lists
        patch('questionary.select', return_value=self.mock_ask).start()
        patch('questionary.text', return_value=self.mock_ask).start()

        # Mock questionary press any key to continue
        patch('questionary.press_any_key_to_continue').start()

        # Mock config file read from disk in tests
        # Note: This effects CliConfigManager singleton (shared between tests)
        self.mock_load = patch(
            'api_client.cli_config.load_node_config_file',
            return_value=mock_ir_config
        )
        self.mock_load.start()

    def tearDown(self):
        # Reset mock to prevent breaking tests in other files
        self.mock_load.stop()

    def test_ir_key_endpoint(self):
        # Simulate user selecting node1, ir, samsung_tv, power
        self.mock_ask.unsafe_ask.side_effect = [
            'node1',
            'ir',
            'samsung_tv',
            'power',
            'Done',
            'Done'
        ]

        # Mock parse_command to return status, then existing macros, then
        # API response from ESP32, then status again (prompt restarts)
        with patch('api_client.parse_command', side_effect=[
            mock_ir_status,
            mock_ir_config['ir_blaster']['macros'],
            {'samsung_tv': 'power'},
            mock_ir_status
        ]) as mock_parse_command:

            # Run prompt, will complete immediately with mock input
            api_prompt()

            # Confirm called parse_command 4 times
            self.assertEqual(mock_parse_command.call_count, 4)

            # First call: requested status object from target node
            self.assertEqual(
                mock_parse_command.call_args_list[0][0],
                ("192.168.1.123", ["status"])
            )

            # Second call: requested existing IR macros
            self.assertEqual(
                mock_parse_command.call_args_list[1][0],
                ("192.168.1.123", ["ir_get_existing_macros"])
            )

            # Third call: sent enable command with correct arg
            self.assertEqual(
                mock_parse_command.call_args_list[2][0],
                ("192.168.1.123", ["ir", "samsung_tv", "power"])
            )

            # Fourth call: requested updated status object after API call
            self.assertEqual(
                mock_parse_command.call_args_list[3][0],
                ("192.168.1.123", ["status"])
            )

    def test_ir_create_macro_endpoint(self):
        # Simulate user selecting node1, ir_create_macro, typing 'New macro'
        self.mock_ask.unsafe_ask.side_effect = [
            'node1',
            'ir_create_macro',
            'New macro',
            'Done',
            'Done'
        ]

        # Mock parse_command to return status, then existing macros, then
        # API response from ESP32, then status again (prompt restarts)
        with patch('api_client.parse_command', side_effect=[
            mock_ir_status,
            mock_ir_config['ir_blaster']['macros'],
            {'Macro created': 'New macro'},
            mock_ir_status
        ]) as mock_parse_command:

            # Run prompt, will complete immediately with mock input
            api_prompt()

            # Confirm called parse_command 4 times
            self.assertEqual(mock_parse_command.call_count, 4)

            # First call: requested status object from target node
            self.assertEqual(
                mock_parse_command.call_args_list[0][0],
                ("192.168.1.123", ["status"])
            )

            # Second call: requested existing IR macros
            self.assertEqual(
                mock_parse_command.call_args_list[1][0],
                ("192.168.1.123", ["ir_get_existing_macros"])
            )

            # Third call: sent enable command with correct arg
            self.assertEqual(
                mock_parse_command.call_args_list[2][0],
                ("192.168.1.123", ["ir_create_macro", "New macro"])
            )

            # Fourth call: requested updated status object after API call
            self.assertEqual(
                mock_parse_command.call_args_list[3][0],
                ("192.168.1.123", ["status"])
            )

    def test_ir_delete_macro_endpoint(self):
        # Simulate user selecting node1, ir_delete_macro, start_ac
        self.mock_ask.unsafe_ask.side_effect = [
            'node1',
            'ir_delete_macro',
            'start_ac',
            'Done',
            'Done'
        ]

        # Mock parse_command to return status, then existing macros, then
        # API response from ESP32, then status again (prompt restarts)
        with patch('api_client.parse_command', side_effect=[
            mock_ir_status,
            mock_ir_config['ir_blaster']['macros'],
            {'Macro deleted': 'start_ac'},
            mock_ir_status
        ]) as mock_parse_command:

            # Run prompt, will complete immediately with mock input
            api_prompt()

            # Confirm called parse_command 4 times
            self.assertEqual(mock_parse_command.call_count, 4)

            # First call: requested status object from target node
            self.assertEqual(
                mock_parse_command.call_args_list[0][0],
                ("192.168.1.123", ["status"])
            )

            # Second call: requested existing IR macros
            self.assertEqual(
                mock_parse_command.call_args_list[1][0],
                ("192.168.1.123", ["ir_get_existing_macros"])
            )

            # Third call: sent enable command with correct arg
            self.assertEqual(
                mock_parse_command.call_args_list[2][0],
                ("192.168.1.123", ["ir_delete_macro", "start_ac"])
            )

            # Fourth call: requested updated status object after API call
            self.assertEqual(
                mock_parse_command.call_args_list[3][0],
                ("192.168.1.123", ["status"])
            )

    def test_ir_add_macro_action_endpoint(self):
        # Simulate user selecting node1, ir_add_macro_action, start_ac, samsung_tv,
        # power, then entering 500 for delay and 2 for repeat args
        self.mock_ask.unsafe_ask.side_effect = [
            'node1',
            'ir_add_macro_action',
            'start_ac',
            'samsung_tv',
            'power',
            '500',
            '2',
            'Done',
            'Done'
        ]

        # Mock questionary.confirm (yes/no prompt for optional args)
        # Mock parse_command to return status, then existing macros, then
        # API response from ESP32, then status again (prompt restarts)
        with patch('questionary.confirm', MagicMock()) as mock_confirm, \
             patch('api_client.parse_command', side_effect=[
                 mock_ir_status,
                 mock_ir_config['ir_blaster']['macros'],
                 {'Macro action added': ['start_ac', 'samsung_tv', 'power', '500', '2']},
                 mock_ir_status
             ]) as mock_parse_command:

            # Answer Yes to optional arg prompts
            mock_confirm.return_value.unsafe_ask.return_value = True

            # Run prompt, will complete immediately with mock input
            api_prompt()

            # Confirm called parse_command 4 times
            self.assertEqual(mock_parse_command.call_count, 4)

            # First call: requested status object from target node
            self.assertEqual(
                mock_parse_command.call_args_list[0][0],
                ("192.168.1.123", ["status"])
            )

            # Second call: requested existing IR macros
            self.assertEqual(
                mock_parse_command.call_args_list[1][0],
                ("192.168.1.123", ["ir_get_existing_macros"])
            )

            # Third call: sent enable command with correct arg
            self.assertEqual(
                mock_parse_command.call_args_list[2][0],
                (
                    "192.168.1.123",
                    [
                        "ir_add_macro_action",
                        "start_ac",
                        "samsung_tv",
                        "power",
                        "500",
                        "2"
                    ]
                )
            )

            # Fourth call: requested updated status object after API call
            self.assertEqual(
                mock_parse_command.call_args_list[3][0],
                ("192.168.1.123", ["status"])
            )

    def test_ir_add_macro_action_endpoint_default_delay_and_repeat(self):
        # Simulate user selecting node1, ir_add_macro_action, start_ac, samsung_tv, power
        self.mock_ask.unsafe_ask.side_effect = [
            'node1',
            'ir_add_macro_action',
            'start_ac',
            'samsung_tv',
            'power',
            'Done',
            'Done'
        ]

        # Mock questionary.confirm (yes/no prompt for optional args)
        # Mock parse_command to return status, then existing macros, then
        # API response from ESP32, then status again (prompt restarts)
        with patch('questionary.confirm', MagicMock()) as mock_confirm, \
             patch('api_client.parse_command', side_effect=[
                 mock_ir_status,
                 mock_ir_config['ir_blaster']['macros'],
                 {'Macro action added': ['start_ac', 'samsung_tv', 'power', '0', '1']},
                 mock_ir_status
             ]) as mock_parse_command:

            # Answer No to optional arg prompts
            mock_confirm.return_value.unsafe_ask.return_value = False

            # Run prompt, will complete immediately with mock input
            api_prompt()

            # Confirm called parse_command 4 times
            self.assertEqual(mock_parse_command.call_count, 4)

            # First call: requested status object from target node
            self.assertEqual(
                mock_parse_command.call_args_list[0][0],
                ("192.168.1.123", ["status"])
            )

            # Second call: requested existing IR macros
            self.assertEqual(
                mock_parse_command.call_args_list[1][0],
                ("192.168.1.123", ["ir_get_existing_macros"])
            )

            # Third call: sent enable command with correct arg
            self.assertEqual(
                mock_parse_command.call_args_list[2][0],
                (
                    "192.168.1.123",
                    [
                        "ir_add_macro_action",
                        "start_ac",
                        "samsung_tv",
                        "power",
                        0,
                        1
                    ]
                )
            )

            # Fourth call: requested updated status object after API call
            self.assertEqual(
                mock_parse_command.call_args_list[3][0],
                ("192.168.1.123", ["status"])
            )

    def test_ir_run_macro_endpoint(self):
        # Simulate user selecting node1, ir_run_macro, start_ac
        self.mock_ask.unsafe_ask.side_effect = [
            'node1',
            'ir_run_macro',
            'start_ac',
            'Done',
            'Done'
        ]

        # Mock parse_command to return status, then existing macros, then
        # API response from ESP32, then status again (prompt restarts)
        with patch('api_client.parse_command', side_effect=[
            mock_ir_status,
            mock_ir_config['ir_blaster']['macros'],
            {'Ran macro': 'start_ac'},
            mock_ir_status
        ]) as mock_parse_command:

            # Run prompt, will complete immediately with mock input
            api_prompt()

            # Confirm called parse_command 4 times
            self.assertEqual(mock_parse_command.call_count, 4)

            # First call: requested status object from target node
            self.assertEqual(
                mock_parse_command.call_args_list[0][0],
                ("192.168.1.123", ["status"])
            )

            # Second call: requested existing IR macros
            self.assertEqual(
                mock_parse_command.call_args_list[1][0],
                ("192.168.1.123", ["ir_get_existing_macros"])
            )

            # Third call: sent enable command with correct arg
            self.assertEqual(
                mock_parse_command.call_args_list[2][0],
                ("192.168.1.123", ["ir_run_macro", "start_ac"])
            )

            # Fourth call: requested updated status object after API call
            self.assertEqual(
                mock_parse_command.call_args_list[3][0],
                ("192.168.1.123", ["status"])
            )

    def test_ir_get_existing_macros_endpoint(self):
        # Simulate user selecting node1, ir_get_existing_macros
        self.mock_ask.unsafe_ask.side_effect = [
            'node1',
            'ir_get_existing_macros',
            'Done',
            'Done'
        ]

        # Mock parse_command to return status, then existing macros, then
        # API response from ESP32, then status again (prompt restarts)
        with patch('api_client.parse_command', side_effect=[
            mock_ir_status,
            mock_ir_config['ir_blaster']['macros'],
            mock_ir_config['ir_blaster']['macros'],
            mock_ir_status
        ]) as mock_parse_command:

            # Run prompt, will complete immediately with mock input
            api_prompt()

            # Confirm called parse_command 4 times
            self.assertEqual(mock_parse_command.call_count, 4)

            # First call: requested status object from target node
            self.assertEqual(
                mock_parse_command.call_args_list[0][0],
                ("192.168.1.123", ["status"])
            )

            # Second call: requested existing IR macros
            self.assertEqual(
                mock_parse_command.call_args_list[1][0],
                ("192.168.1.123", ["ir_get_existing_macros"])
            )

            # Third call: requested ir_get_existing_macros
            self.assertEqual(
                mock_parse_command.call_args_list[2][0],
                ("192.168.1.123", ["ir_get_existing_macros"])
            )

            # Fourth call: requested updated status object after API call
            self.assertEqual(
                mock_parse_command.call_args_list[3][0],
                ("192.168.1.123", ["status"])
            )


class RegressionTests(TestCase):
    def setUp(self):
        # Mock replaces .unsafe_ask() method to simulate user input
        # Each test sets side_effect with list of simulated user inputs
        self.mock_ask = MagicMock()

        # Mock questionary prompts to return the next item in mock_ask lists
        patch('questionary.select', return_value=self.mock_ask).start()
        patch('questionary.text', return_value=self.mock_ask).start()

        # Mock questionary press any key to continue
        patch('questionary.press_any_key_to_continue').start()

        # Mock config file read from disk in tests
        # Note: This effects CliConfigManager singleton (shared between tests)
        self.mock_load = patch(
            'api_client.cli_config.load_node_config_file',
            return_value=mock_config
        )
        self.mock_load.start()

    def tearDown(self):
        # Reset mock to prevent breaking tests in other files
        self.mock_load.stop()

    def test_status_command_failed(self):
        '''Original bug: An unhandled TypeError was raised if a connection
        error occurred during status request at the top of api_prompt loop.
        This happened when the error string was passed to get_endpoint_options,
        which expects a status dict and tries to access keys within dict.
        '''

        # Simulate user selecting node1, set_rule, device1, Fade, and entering
        # target=1023 duration=15 (lots of steps and short duration bottlenecks
        # ESP32 and causes next request to time out).
        #
        # Do not simulate selecting 'Done' (prompt exits when request fails)
        self.mock_ask.unsafe_ask.side_effect = [
            'node1',
            'set_rule',
            'device1',
            'Fade',
            '1023',
            '15'
        ]

        # Mock parse_command to return status, timeout error (in response to
        # set_rule), then timeout error again (in response to status request)
        with patch('api_client.parse_command', side_effect=[
                mock_status_object,
                "Error: Timed out waiting for response",
                "Error: Timed out waiting for response"
            ]):  # noqa: E122

            # Run prompt, will complete immediately with mock input
            # Should not raise TypeError after fix
            api_prompt()

    def test_device_or_sensor_rule_prompt_missing_config_file(self):
        '''Original bug: When endpoints that call device_or_sensor_rule_prompt
        were selected for a node with config file missing from disk an uncaught
        FileNotFoundError occurred, causing the client to exit.
        '''

        # Mock load_node_config_file to raise FileNotFoundError (missing config)
        with patch(
            'api_client.cli_config.load_node_config_file',
            side_effect=FileNotFoundError
        ):
            # Confirm method returns None instead of raising exception
            self.assertIsNone(
                device_or_sensor_rule_prompt('node-name', 'device1')
            )


class GetEndpointOptionsTests(TestCase):
    def test_no_devices_or_sensors(self):
        # Call function with status with no devices or sensors
        options = get_endpoint_options({
            'metadata': {
                'ir_blaster': False
            },
            'devices': {},
            'sensors': {}
        })

        # Confirm options do not include device/sensor/IrBlaster endpoints
        self.assertEqual(
            options,
            [
                'reboot',
                'get_schedule_keywords',
                'add_schedule_keyword',
                'remove_schedule_keyword',
                'save_schedule_keywords',
                'clear_log',
                'set_log_level',
                'set_gps_coords',
                'mem_info',
                'Done'
            ]
        )

    def test_no_devices(self):
        # Call function with status containing sensors but no devices
        options = get_endpoint_options({
            'metadata': {
                'ir_blaster': False
            },
            'devices': {},
            'sensors': {
                'sensor1': {
                    'type': 'pir'
                }
            }
        })

        # Confirm options do not include device or IrBlaster endpoints, but do
        # contain sensor endpoints (condition_met, trigger_sensor)
        self.assertEqual(
            options,
            [
                'reboot',
                'disable',
                'disable_in',
                'enable',
                'enable_in',
                'set_rule',
                'increment_rule',
                'reset_rule',
                'reset_all_rules',
                'get_schedule_rules',
                'add_rule',
                'remove_rule',
                'save_rules',
                'get_schedule_keywords',
                'add_schedule_keyword',
                'remove_schedule_keyword',
                'save_schedule_keywords',
                'get_attributes',
                'clear_log',
                'set_log_level',
                'condition_met',
                'trigger_sensor',
                'set_gps_coords',
                'mem_info',
                'Done'
            ]
        )

    def test_no_sensors(self):
        # Call function with status containing devices but no sensors
        options = get_endpoint_options({
            'metadata': {
                'ir_blaster': False
            },
            'devices': {
                'device1': {
                    'type': 'pwm'
                }
            },
            'sensors': {}
        })

        # Confirm options do not include sensor or IrBlaster endpoints, but do
        # contain device endpoints (turn_on, turn_off)
        self.assertEqual(
            options,
            [
                'reboot',
                'disable',
                'disable_in',
                'enable',
                'enable_in',
                'set_rule',
                'increment_rule',
                'reset_rule',
                'reset_all_rules',
                'get_schedule_rules',
                'add_rule',
                'remove_rule',
                'save_rules',
                'get_schedule_keywords',
                'add_schedule_keyword',
                'remove_schedule_keyword',
                'save_schedule_keywords',
                'get_attributes',
                'clear_log',
                'set_log_level',
                'turn_on',
                'turn_off',
                'set_gps_coords',
                'mem_info',
                'Done'
            ]
        )

    def test_ir_blaster(self):
        # Call function with status with ir_blaster configured
        options = get_endpoint_options({
            'metadata': {
                'ir_blaster': True
            },
            'devices': {},
            'sensors': {}
        })

        # Confirm options do not include device/sensor endpoints but do include
        # IR Blaster endpoints
        self.assertEqual(
            options,
            [
                'reboot',
                'get_schedule_keywords',
                'add_schedule_keyword',
                'remove_schedule_keyword',
                'save_schedule_keywords',
                'ir',
                'ir_get_existing_macros',
                'ir_create_macro',
                'ir_delete_macro',
                'ir_save_macros',
                'ir_add_macro_action',
                'ir_run_macro',
                'clear_log',
                'set_log_level',
                'set_gps_coords',
                'mem_info',
                'Done'
            ]
        )

    def test_temperature_sensor(self):
        # Call function with status containing temperature sensor
        options = get_endpoint_options({
            'metadata': {
                'ir_blaster': False
            },
            'devices': {},
            'sensors': {
                'sensor1': {
                    'type': 'si7021'
                }
            }
        })

        # Confirm options include temperature sensor endpoints (get_temp,
        # get_humid, get_climate) and sensor endpoints (condition_met, trigger_sensor)
        self.assertEqual(
            options,
            [
                'reboot',
                'disable',
                'disable_in',
                'enable',
                'enable_in',
                'set_rule',
                'increment_rule',
                'reset_rule',
                'reset_all_rules',
                'get_schedule_rules',
                'add_rule',
                'remove_rule',
                'save_rules',
                'get_schedule_keywords',
                'add_schedule_keyword',
                'remove_schedule_keyword',
                'save_schedule_keywords',
                'get_attributes',
                'get_temp',
                'get_humid',
                'get_climate',
                'clear_log',
                'set_log_level',
                'condition_met',
                'trigger_sensor',
                'set_gps_coords',
                'mem_info',
                'Done'
            ]
        )

    def test_load_cell_sensor(self):
        # Call function with status containing load cell sensor
        options = get_endpoint_options({
            'metadata': {
                'ir_blaster': False
            },
            'devices': {},
            'sensors': {
                'sensor1': {
                    'type': 'load-cell'
                }
            }
        })

        # Confirm options include load cell endpoints (load_cell_tare,
        # load_cell_read) and sensor endpoints (condition_met, trigger_sensor)
        self.assertEqual(
            options,
            [
                'reboot',
                'disable',
                'disable_in',
                'enable',
                'enable_in',
                'set_rule',
                'increment_rule',
                'reset_rule',
                'reset_all_rules',
                'get_schedule_rules',
                'add_rule',
                'remove_rule',
                'save_rules',
                'get_schedule_keywords',
                'add_schedule_keyword',
                'remove_schedule_keyword',
                'save_schedule_keywords',
                'get_attributes',
                'clear_log',
                'set_log_level',
                'condition_met',
                'trigger_sensor',
                'set_gps_coords',
                'load_cell_tare',
                'load_cell_read',
                'mem_info',
                'Done'
            ]
        )
