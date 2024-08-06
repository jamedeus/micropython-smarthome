import os
import sys
import json
import asyncio
from io import StringIO
from unittest import TestCase
from unittest.mock import patch, MagicMock, AsyncMock
from questionary import ValidationError
from api_client import api_prompt, parse_command, main
from api_endpoints import ir_commands, request
from test_api_client import mock_cli_config, mock_status_object

# Get paths to test dir, CLI dir, repo dir
tests = os.path.dirname(os.path.realpath(__file__))
cli = os.path.split(tests)[0]
repo = os.path.dirname(tests)

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
        # Mock replaces .ask() method to simulate user input
        self.mock_ask = MagicMock()

    def test_enable_endpoint(self):
        # Simulate user selecting node1, enable, sensor1
        self.mock_ask.unsafe_ask.side_effect = [
            'node1',
            'enable',
            'sensor1',
            'Done',
            'Done'
        ]
        with patch("sys.argv", ["api_client.py"]), \
             patch('api_client.nodes', mock_cli_config['nodes']), \
             patch('questionary.select', return_value=self.mock_ask), \
             patch('questionary.press_any_key_to_continue'), \
             patch('api_client.parse_command', return_value=mock_status_object) as mock_parse_command:

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
        with patch("sys.argv", ["api_client.py"]), \
             patch('api_client.nodes', mock_cli_config['nodes']), \
             patch('questionary.text', return_value=self.mock_ask), \
             patch('questionary.select', return_value=self.mock_ask), \
             patch('questionary.press_any_key_to_continue'), \
             patch('api_client.parse_command', return_value=mock_status_object) as mock_parse_command:

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
        with patch("sys.argv", ["api_client.py"]), \
             patch('api_client.nodes', mock_cli_config['nodes']), \
             patch('questionary.text', return_value=self.mock_ask), \
             patch('questionary.select', return_value=self.mock_ask), \
             patch('questionary.press_any_key_to_continue'), \
             patch('api_client.load_node_config_file', return_value=mock_config), \
             patch('api_client.parse_command', return_value=mock_status_object) as mock_parse_command:

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
        with patch("sys.argv", ["api_client.py"]), \
             patch('api_client.nodes', mock_cli_config['nodes']), \
             patch('questionary.text', return_value=self.mock_ask), \
             patch('questionary.select', return_value=self.mock_ask), \
             patch('questionary.press_any_key_to_continue'), \
             patch('api_client.parse_command', return_value=mock_status_object) as mock_parse_command:

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
        with patch("sys.argv", ["api_client.py"]), \
             patch('api_client.nodes', mock_cli_config['nodes']), \
             patch('questionary.text', return_value=self.mock_ask), \
             patch('questionary.select', return_value=self.mock_ask), \
             patch('questionary.press_any_key_to_continue'), \
             patch('api_client.load_node_config_file', return_value=mock_config), \
             patch('api_client.parse_command', return_value=mock_status_object) as mock_parse_command:

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
        with patch("sys.argv", ["api_client.py"]), \
             patch('api_client.nodes', mock_cli_config['nodes']), \
             patch('questionary.text', return_value=self.mock_ask), \
             patch('questionary.select', return_value=self.mock_ask), \
             patch('questionary.press_any_key_to_continue'), \
             patch('api_client.load_node_config_file', return_value=mock_config), \
             patch('api_client.parse_command', return_value=mock_status_object) as mock_parse_command:

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

    def test_turn_on_endpoint(self):
        # Simulate user selecting node1, turn_on, device1
        self.mock_ask.unsafe_ask.side_effect = [
            'node1',
            'turn_on',
            'device1',
            'Done',
            'Done'
        ]
        with patch("sys.argv", ["api_client.py"]), \
             patch('api_client.nodes', mock_cli_config['nodes']), \
             patch('questionary.select', return_value=self.mock_ask), \
             patch('questionary.press_any_key_to_continue'), \
             patch('api_client.parse_command', return_value=mock_status_object) as mock_parse_command:

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
        with patch("sys.argv", ["api_client.py"]), \
             patch('api_client.nodes', mock_cli_config['nodes']), \
             patch('questionary.select', return_value=self.mock_ask), \
             patch('questionary.press_any_key_to_continue'), \
             patch('api_client.parse_command', return_value=mock_status_object) as mock_parse_command:

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
        with patch("sys.argv", ["api_client.py"]), \
             patch('api_client.nodes', mock_cli_config['nodes']), \
             patch('questionary.text', return_value=self.mock_ask), \
             patch('questionary.select', return_value=self.mock_ask), \
             patch('questionary.press_any_key_to_continue'), \
             patch('api_client.load_node_config_file', return_value=mock_config), \
             patch('api_client.parse_command', return_value=mock_status_object) as mock_parse_command:

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
        with patch("sys.argv", ["api_client.py"]), \
             patch('api_client.nodes', mock_cli_config['nodes']), \
             patch('questionary.text', return_value=self.mock_ask), \
             patch('questionary.select', return_value=self.mock_ask), \
             patch('questionary.press_any_key_to_continue'), \
             patch('api_client.load_node_config_file', return_value=mock_config), \
             patch('api_client.parse_command', return_value=mock_status_object) as mock_parse_command:

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
        with patch("sys.argv", ["api_client.py"]), \
             patch('api_client.nodes', mock_cli_config['nodes']), \
             patch('questionary.text', return_value=self.mock_ask), \
             patch('questionary.select', return_value=self.mock_ask), \
             patch('questionary.press_any_key_to_continue'), \
             patch('api_client.load_node_config_file', return_value=mock_config), \
             patch('api_client.parse_command', return_value=mock_status_object) as mock_parse_command:

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
        self.mock_ask.unsafe_ask.side_effect = [
            'Done'
        ]

        # Patch empty sys.argv (runs interactive menu when main called)
        with patch("sys.argv", ["api_client.py"]), \
             patch('api_client.nodes', mock_cli_config['nodes']), \
             patch('questionary.select', return_value=self.mock_ask), \
             patch('api_client.parse_command') as mock_parse_command:

            # Call main, will run interactive menu (blank sys.argv)
            main()

            # Confirm parse_command was not called
            self.assertEqual(mock_parse_command.call_count, 0)


class InteractiveIrBlasterMenuTests(TestCase):
    def setUp(self):
        # Mock replaces .ask() method to simulate user input
        self.mock_ask = MagicMock()

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
        with patch("sys.argv", ["api_client.py"]), \
             patch('api_client.nodes', mock_cli_config['nodes']), \
             patch('questionary.text', return_value=self.mock_ask), \
             patch('questionary.select', return_value=self.mock_ask), \
             patch('questionary.press_any_key_to_continue'), \
             patch('api_client.load_node_config_file', return_value=mock_ir_config), \
             patch('api_client.parse_command', return_value=mock_ir_status) as mock_parse_command:

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
        with patch("sys.argv", ["api_client.py"]), \
             patch('api_client.nodes', mock_cli_config['nodes']), \
             patch('questionary.text', return_value=self.mock_ask), \
             patch('questionary.select', return_value=self.mock_ask), \
             patch('questionary.press_any_key_to_continue'), \
             patch('api_client.load_node_config_file', return_value=mock_ir_config), \
             patch('api_client.parse_command', return_value=mock_ir_status) as mock_parse_command:

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

        # Mock parse_command to return status, then macros, then status
        mock_api_responses = [
            mock_ir_status,
            mock_ir_config['ir_blaster']['macros'],
            mock_ir_status,
            mock_ir_status
        ]

        with patch("sys.argv", ["api_client.py"]), \
             patch('api_client.nodes', mock_cli_config['nodes']), \
             patch('questionary.text', return_value=self.mock_ask), \
             patch('questionary.select', return_value=self.mock_ask), \
             patch('questionary.press_any_key_to_continue'), \
             patch('api_client.load_node_config_file', return_value=mock_ir_config), \
             patch('api_client.parse_command', side_effect=mock_api_responses) as mock_parse_command:

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

        # Mock parse_command to return status, then macros, then status
        mock_api_responses = [
            mock_ir_status,
            mock_ir_config['ir_blaster']['macros'],
            mock_ir_status,
            mock_ir_status
        ]

        with patch("sys.argv", ["api_client.py"]), \
             patch('api_client.nodes', mock_cli_config['nodes']), \
             patch('questionary.text', return_value=self.mock_ask), \
             patch('questionary.select', return_value=self.mock_ask), \
             patch('questionary.confirm', MagicMock()) as mock_confirm, \
             patch('questionary.press_any_key_to_continue'), \
             patch('api_client.load_node_config_file', return_value=mock_ir_config), \
             patch('api_client.parse_command', side_effect=mock_api_responses) as mock_parse_command:

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

        # Mock parse_command to return status, then macros, then status
        mock_api_responses = [
            mock_ir_status,
            mock_ir_config['ir_blaster']['macros'],
            mock_ir_status,
            mock_ir_status
        ]

        with patch("sys.argv", ["api_client.py"]), \
             patch('api_client.nodes', mock_cli_config['nodes']), \
             patch('questionary.text', return_value=self.mock_ask), \
             patch('questionary.select', return_value=self.mock_ask), \
             patch('questionary.confirm', MagicMock()) as mock_confirm, \
             patch('questionary.press_any_key_to_continue'), \
             patch('api_client.load_node_config_file', return_value=mock_ir_config), \
             patch('api_client.parse_command', side_effect=mock_api_responses) as mock_parse_command:

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

        # Mock parse_command to return status, then macros, then status
        mock_api_responses = [
            mock_ir_status,
            mock_ir_config['ir_blaster']['macros'],
            mock_ir_status,
            mock_ir_status
        ]

        with patch("sys.argv", ["api_client.py"]), \
             patch('api_client.nodes', mock_cli_config['nodes']), \
             patch('questionary.text', return_value=self.mock_ask), \
             patch('questionary.select', return_value=self.mock_ask), \
             patch('questionary.press_any_key_to_continue'), \
             patch('api_client.load_node_config_file', return_value=mock_ir_config), \
             patch('api_client.parse_command', side_effect=mock_api_responses) as mock_parse_command:

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
