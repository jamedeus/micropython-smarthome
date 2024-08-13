'''Unit tests for the interactive menu shown when api_client.py is called from
the command line with no arguments.
'''

# pylint: disable=missing-function-docstring, missing-class-docstring

from unittest import TestCase
from unittest.mock import patch, MagicMock
from api_client import api_prompt, main
from mock_cli_config import mock_cli_config
from test_api_client import mock_status_object

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
            "tv",
            "ac"
        ],
        "macros": {
            "start_ac": [
                ("ac", "on", "100", "1"),
                ("ac", "start", "0", "1")
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
            'tv',
            'ac'
        ],
        "schedule_keywords": {
            "sunrise": "06:00",
            "sunset": "18:00",
            "sleep": "23:00"
        }
    }
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
        self.mock_ask.unsafe_ask.side_effect = [
            'node1',
            'reboot',
            'Done',
            'Done'
        ]

        # Mock parse_command to return status, then API response from ESP32,
        # then status again (prompt restarts)
        with patch('api_client.parse_command', side_effect=[
            mock_status_object,
            mock_status_object,
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

            # Second call: sent reboot command
            self.assertEqual(
                mock_parse_command.call_args_list[1][0],
                ("192.168.1.123", ["reboot"])
            )

            # Third call: requested updated status object after API call
            self.assertEqual(
                mock_parse_command.call_args_list[2][0],
                ("192.168.1.123", ["status"])
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
        # Simulate user selecting node1, ir, tv, power
        self.mock_ask.unsafe_ask.side_effect = [
            'node1',
            'ir',
            'tv',
            'power',
            'Done',
            'Done'
        ]

        # Mock parse_command to return status, then existing macros, then
        # API response from ESP32, then status again (prompt restarts)
        with patch('api_client.parse_command', side_effect=[
            mock_ir_status,
            mock_ir_config['ir_blaster']['macros'],
            {'tv': 'power'},
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
                ("192.168.1.123", ["ir", "tv", "power"])
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
        # Simulate user selecting node1, ir_add_macro_action, start_ac, tv,
        # power, then entering 500 for delay and 2 for repeat args
        self.mock_ask.unsafe_ask.side_effect = [
            'node1',
            'ir_add_macro_action',
            'start_ac',
            'tv',
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
            {'Macro action added': ['start_ac', 'tv', 'power', '500', '2']},
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
                ("192.168.1.123", ["ir_add_macro_action", "start_ac", "tv", "power", "500", "2"])
            )

            # Fourth call: requested updated status object after API call
            self.assertEqual(
                mock_parse_command.call_args_list[3][0],
                ("192.168.1.123", ["status"])
            )

    def test_ir_add_macro_action_endpoint_default_delay_and_repeat(self):
        # Simulate user selecting node1, ir_add_macro_action, start_ac, tv, power
        self.mock_ask.unsafe_ask.side_effect = [
            'node1',
            'ir_add_macro_action',
            'start_ac',
            'tv',
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
            {'Macro action added': ['start_ac', 'tv', 'power', '0', '1']},
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
                ("192.168.1.123", ["ir_add_macro_action", "start_ac", "tv", "power", 0, 1])
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
