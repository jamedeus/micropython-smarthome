'''Unit tests for functions called with api_client.py command line arguments'''

# pylint: disable=missing-function-docstring, missing-class-docstring

import sys
import json
import asyncio
from io import StringIO
from unittest import TestCase, IsolatedAsyncioTestCase
from unittest.mock import patch, MagicMock, AsyncMock
from api_client import endpoint_error, parse_ip, parse_command, main, example_usage_error
from api_endpoints import ir_commands, request
from mock_cli_config import mock_cli_config

mock_status_object = {
    'metadata': {
        'id': 'Test1',
        'floor': '1',
        'location': 'Inside cabinet above microwave',
        'ir_blaster': False,
        "schedule_keywords": {
            "sunrise": "06:00",
            "sunset": "18:00",
            "sleep": "23:00"
        }
    },
    'sensors': {
        'sensor1': {
            'current_rule': 2.0,
            'enabled': True,
            'type': 'pir',
            'targets': [
                'device1',
                'device2'
            ],
            'schedule': {
                '10:00': '2',
                '22:00': '2'
            },
            'scheduled_rule': 2.0,
            'nickname': 'Motion Sensor',
            'condition_met': True
        }
    },
    'devices': {
        'device1': {
            'current_rule': 'disabled',
            'enabled': False,
            'type': 'pwm',
            'schedule': {
                '00:00': 'fade/32/7200',
                '05:00': 'Disabled',
                '22:01': 'fade/256/7140',
                '22:00': '1023'
            },
            'scheduled_rule': 'disabled',
            'nickname': 'Cabinet Lights',
            'turned_on': True
        },
        'device2': {
            'current_rule': 'enabled',
            'enabled': True,
            'type': 'tasmota-relay',
            'schedule': {
                '05:00': 'enabled',
                '22:00': 'disabled'
            },
            'scheduled_rule': 'enabled',
            'nickname': 'Overhead Lights',
            'turned_on': True
        }
    }
}


class TestError(TestCase):

    def test_error(self):
        with self.assertRaises(SystemExit):
            endpoint_error()


# Test function that makes async API calls to esp32 nodes (called by all endpoint functions)
class RequestTests(IsolatedAsyncioTestCase):
    def setUp(self):
        # Simulate successful reply from Node
        async def read_response():
            return b'{"Enabled": "device1"}'

        # Simulate invalid reply from Node
        async def read_response_fail():
            raise OSError

        # Simulate read call that hangs forever
        async def read_response_hang():
            await asyncio.Event().wait()

        # Create mock asyncio reader that returns successful response
        mock_reader = MagicMock()
        mock_reader.read = AsyncMock(side_effect=read_response)

        # Create mock asyncio reader that fails to read response
        mock_reader_fail = MagicMock()
        mock_reader_fail.read = AsyncMock(side_effect=read_response_fail)

        # Create mock asyncio reader that hangs (target node connected, but event loop crashed)
        mock_reader_hang = MagicMock()
        mock_reader_hang.read = AsyncMock(side_effect=read_response_hang)

        # Create mock asyncio writer that does nothing
        mock_writer = MagicMock()
        mock_writer.drain = AsyncMock()
        mock_writer.write = MagicMock()
        mock_writer.wait_closed = AsyncMock()

        # Mock open_connection to return mock_reader + mock_writer
        async def mock_open_connection(*args, **kwargs):
            return mock_reader, mock_writer

        # Mock open_connection to return mock_reader_fail + mock_writer
        async def mock_open_connection_fail(*args, **kwargs):
            return mock_reader_fail, mock_writer

        # Mock open_connection to return mock_reader_hang + mock_writer
        async def mock_open_connection_hang(*args, **kwargs):
            return mock_reader_hang, mock_writer

        # Mock wait_for to return immediately
        async def mock_wait_for(coro, timeout):
            return await coro

        # Make accessible in test methods
        self.mock_open_connection = mock_open_connection
        self.mock_open_connection_fail = mock_open_connection_fail
        self.mock_open_connection_hang = mock_open_connection_hang
        self.mock_wait_for = mock_wait_for

    async def test_request_successful(self):
        # Mock asyncio methods to simulate successful connection
        with patch('api_endpoints.asyncio.open_connection', side_effect=self.mock_open_connection), \
             patch('api_endpoints.asyncio.wait_for', side_effect=self.mock_wait_for):

            # Send request, verify response
            response = await request('192.168.1.123', ['enable', 'device1'])
            self.assertEqual(response, {'Enabled': 'device1'})

    async def test_request_connection_errors(self):
        # Simulate timed out connection (target node event loop blocked)
        with patch('api_endpoints.asyncio.wait_for', side_effect=asyncio.TimeoutError):

            # Make request, verify error
            response = await request('192.168.1.123', ['enable', 'device1'])
            self.assertEqual(response, "Error: Request timed out")

        # Simulate failed connection (target node offline, wrong IP, etc)
        with patch('api_endpoints.asyncio.wait_for', side_effect=OSError):

            # Make request, verify error
            response = await request('192.168.1.123', ['enable', 'device1'])
            self.assertEqual(response, "Error: Failed to connect")

        # Simulate successful connection, failed write
        with patch('api_endpoints.asyncio.open_connection', side_effect=self.mock_open_connection_fail), \
             patch('api_endpoints.asyncio.wait_for', side_effect=self.mock_wait_for):

            # Make request, verify error
            response = await request('192.168.1.123', ['enable', 'device1'])
            self.assertEqual(response, "Error: Request failed")

        # Simulate successful connection, receive invalid response
        with patch('api_endpoints.asyncio.open_connection', side_effect=self.mock_open_connection), \
             patch('api_endpoints.asyncio.wait_for', side_effect=self.mock_wait_for), \
             patch('api_client.json.loads', side_effect=ValueError):

            # Make request, verify error
            response = await request('192.168.1.123', ['enable', 'device1'])
            self.assertEqual(response, "Error: Unable to decode response")

    # Original issue: Timeout on open_connection worked for offline nodes, but
    # not crashed nodes. After event loop crash node remains on wifi, so
    # connection succeeds but node never responds and read call hangs forever.
    # Fixed by adding timeout to read call.
    async def test_regression_crashed_target_node(self):
        # Simulate hanging read after successful connection (target node event loop crashed)
        with patch('api_endpoints.asyncio.open_connection', side_effect=self.mock_open_connection_hang):
            # Send request, verify error
            # Request wrapped in 6 second timeout to prevent hanging in case of failure
            response = await asyncio.wait_for(request('192.168.1.123', ['enable', 'device1']), timeout=6)
            self.assertEqual(response, "Error: Timed out waiting for response")


# Test function that takes all args, finds IP, and passes IP + remaining args to parse_command
class TestParseIP(TestCase):

    def test_all_flag(self):
        with patch('api_client.parse_command', return_value={"Enabled": "device1"}) as mock_parse_command, \
             self.assertRaises(SystemExit):

            # Parse args, should call parse_command once for each node before exiting
            self.assertTrue(parse_ip(['--all', 'enable', 'device1']))
            self.assertEqual(mock_parse_command.call_count, len(mock_cli_config['nodes']))

    def test_node_name(self):
        with patch('api_client.parse_command', return_value={"Enabled": "device1"}) as mock_parse_command:

            self.assertTrue(parse_ip(['node2', 'enable', 'device1']))
            self.assertTrue(mock_parse_command.called_once)

    def test_ip_flag(self):
        with patch('api_client.parse_command', return_value={"Enabled": "device1"}) as mock_parse_command:
            self.assertTrue(parse_ip(['-ip', '192.168.1.123', 'enable', 'device1']))
            self.assertTrue(mock_parse_command.called_once)

    def test_ip_flag_invalid(self):
        with patch('api_client.parse_command', return_value={"Enabled": "device1"}) as mock_parse_command, \
             self.assertRaises(SystemExit):

            self.assertTrue(parse_ip(['-ip', '192.168.1', 'enable', 'device1']))
            self.assertFalse(mock_parse_command.called)

    def test_no_target_ip(self):
        with patch('api_client.parse_command', return_value={"Enabled": "device1"}) as mock_parse_command, \
             self.assertRaises(SystemExit):

            self.assertTrue(parse_ip(['enable', 'device1']))
            self.assertFalse(mock_parse_command.called)

    def test_no_config_file(self):
        with patch("builtins.open", MagicMock(side_effect=FileNotFoundError)), \
             patch('api_client.parse_command', return_value={"Enabled": "device1"}) as mock_parse_command, \
             self.assertRaises(SystemExit):

            self.assertTrue(parse_ip(['--all', 'enable', 'device1']))
            self.assertFalse(mock_parse_command.called)


# Test function that takes IP + command args and calls correct endpoint function
class TestParseCommand(TestCase):

    def test_no_args(self):
        with patch('api_client.endpoint_error', MagicMock(side_effect=SystemExit)) as mock_error, \
             self.assertRaises(SystemExit):

            parse_command('192.168.1.123', [])
            self.assertTrue(mock_error.called)

    def test_invalid_endpoint(self):
        with patch('api_client.endpoint_error', MagicMock(side_effect=SystemExit)) as mock_error, \
             self.assertRaises(SystemExit):

            parse_command('192.168.1.123', ['self_destruct'])
            self.assertTrue(mock_error.called)


# Verify that the correct usage examples are shown for each endpoint when no arguments are provided
class TestExampleUsage(TestCase):

    def test_no_args(self):
        response = parse_ip(['192.168.1.123', 'disable'])
        self.assertEqual(response, {"Example usage": "./api_client.py disable [device|sensor]"})

        response = parse_ip(['192.168.1.123', 'disable_in'])
        self.assertEqual(response, {"Example usage": "./api_client.py disable_in [device|sensor] [minutes]"})

        response = parse_ip(['192.168.1.123', 'enable'])
        self.assertEqual(response, {"Example usage": "./api_client.py enable [device|sensor]"})

        response = parse_ip(['192.168.1.123', 'enable_in'])
        self.assertEqual(response, {"Example usage": "./api_client.py enable_in [device|sensor] [minutes]"})

        response = parse_ip(['192.168.1.123', 'set_rule'])
        self.assertEqual(response, {"Example usage": "./api_client.py set_rule [device|sensor] [rule]"})

        response = parse_ip(['192.168.1.123', 'increment_rule'])
        self.assertEqual(response, {"Example usage": "./api_client.py increment_rule [device] [int]"})

        response = parse_ip(['192.168.1.123', 'reset_rule'])
        self.assertEqual(response, {"Example usage": "./api_client.py reset_rule [device|sensor]"})

        response = parse_ip(['192.168.1.123', 'get_schedule_rules'])
        self.assertEqual(response, {"Example usage": "./api_client.py get_schedule_rules [device|sensor]"})

        response = parse_ip(['192.168.1.123', 'add_rule'])
        self.assertEqual(response, {"Example usage": "./api_client.py add_rule [device|sensor] [HH:MM] [rule] <overwrite>"})

        response = parse_ip(['192.168.1.123', 'remove_rule'])
        self.assertEqual(response, {"Example usage": "./api_client.py remove_rule [device|sensor] [HH:MM]"})

        response = parse_ip(['192.168.1.123', 'add_schedule_keyword'])
        self.assertEqual(response, {"Example usage": "./api_client.py add_schedule_keyword [keyword] [HH:MM]"})

        response = parse_ip(['192.168.1.123', 'remove_schedule_keyword'])
        self.assertEqual(response, {"Example usage": "./api_client.py remove_schedule_keyword [keyword]"})

        response = parse_ip(['192.168.1.123', 'get_attributes'])
        self.assertEqual(response, {"Example usage": "./api_client.py get_attributes [device|sensor]"})

        response = parse_ip(['192.168.1.123', 'condition_met'])
        self.assertEqual(response, {"Example usage": "./api_client.py condition_met [sensor]"})

        response = parse_ip(['192.168.1.123', 'trigger_sensor'])
        self.assertEqual(response, {"Example usage": "./api_client.py trigger_sensor [sensor]"})

        response = parse_ip(['192.168.1.123', 'turn_on'])
        self.assertEqual(response, {"Example usage": "./api_client.py turn_on [device]"})

        response = parse_ip(['192.168.1.123', 'turn_off'])
        self.assertEqual(response, {"Example usage": "./api_client.py turn_off [device]"})

        response = parse_ip(['192.168.1.123', 'ir'])
        self.assertEqual(response, {"Example usage": "./api_client.py ir [tv|ac] [command]"})

        response = parse_ip(['192.168.1.123', 'set_gps_coords'])
        self.assertEqual(response, {"Example usage": "./api_client.py set_gps_coords [latitude] [longitude]"})

    def test_invalid_endpoint(self):
        # Pass non-existing endpoint to example usage error, should show endpoint error
        with patch('api_client.endpoint_error', MagicMock()) as mock_error:
            example_usage_error('self_destruct')
            self.assertTrue(mock_error.called)


# Test successful calls to all API endpoints (with mocked return values)
class TestEndpoints(TestCase):

    def test_status(self):
        # Mock request to return status object
        with patch('api_endpoints.request', return_value=mock_status_object):
            # Request status, should receive expected object
            response = parse_command('192.168.1.123', ['status'])
            self.assertEqual(response, mock_status_object)

    def test_reboot(self):
        # Mock request to return expected response
        with patch('api_endpoints.request', return_value='Rebooting'):
            # Send request, verify response
            response = parse_command('192.168.1.123', ['reboot'])
            self.assertEqual(response, 'Rebooting')

    def test_disable(self):
        # Mock request to return expected response
        with patch('api_endpoints.request', return_value={'Disabled': 'device1'}):
            # Send request, verify response
            response = parse_command('192.168.1.123', ['disable', 'device1'])
            self.assertEqual(response, {'Disabled': 'device1'})

    def test_disable_in(self):
        # Mock request to return expected response
        with patch('api_endpoints.request', return_value={'Disabled': 'device1', 'Disable_in_seconds': 300.0}):
            # Send request, verify response
            response = parse_command('192.168.1.123', ['disable_in', 'device1', '5'])
            self.assertEqual(response, {'Disabled': 'device1', 'Disable_in_seconds': 300.0})

    def test_enable(self):
        # Mock request to return expected response
        with patch('api_endpoints.request', return_value={'Enabled': 'device1'}):
            # Send request, verify response
            response = parse_command('192.168.1.123', ['enable', 'device1'])
            self.assertEqual(response, {'Enabled': 'device1'})

    def test_enable_in(self):
        # Mock request to return expected response
        with patch('api_endpoints.request', return_value={'Enabled': 'device1', 'Enable_in_seconds': 300.0}):
            # Send request, verify response
            response = parse_command('192.168.1.123', ['enable_in', 'device1', '5'])
            self.assertEqual(response, {'Enabled': 'device1', 'Enable_in_seconds': 300.0})

    def test_set_rule(self):
        # Mock request to return expected response
        with patch('api_endpoints.request', return_value={"device1": "50"}):
            # Send request, verify response
            response = parse_command('192.168.1.123', ['set_rule', 'device1', '50'])
            self.assertEqual(response, {"device1": "50"})

    def test_increment_rule(self):
        # Mock request to return expected response
        with patch('api_endpoints.request', return_value={"device1": "100"}):
            # Send request, verify response
            response = parse_command('192.168.1.123', ['increment_rule', 'device1', '50'])
            self.assertEqual(response, {"device1": "100"})

    def test_reset_rule(self):
        # Mock request to return expected response
        expected_response = {'device1': 'Reverted to scheduled rule', 'current_rule': 'disabled'}
        with patch('api_endpoints.request', return_value=expected_response):
            # Send request, verify response
            response = parse_command('192.168.1.123', ['reset_rule', 'device1'])
            self.assertEqual(response, expected_response)

    def test_reset_all_rules(self):
        # Mock request to return expected response
        expected_response = {'New rules': {'device1': 'disabled', 'sensor1': 2.0, 'device2': 'enabled'}}
        with patch('api_endpoints.request', return_value=expected_response):
            # Send request, verify response
            response = parse_command('192.168.1.123', ['reset_all_rules'])
            self.assertEqual(response, expected_response)

    def test_get_schedule_rules(self):
        # Mock request to return expected response
        with patch('api_endpoints.request', return_value={'05:00': 'enabled', '22:00': 'disabled'}):
            # Send request, verify response
            response = parse_command('192.168.1.123', ['get_schedule_rules', 'device2'])
            self.assertEqual(response, {'05:00': 'enabled', '22:00': 'disabled'})

    def test_add_rule(self):
        # Mock request to return expected response
        with patch('api_endpoints.request', return_value={'time': '10:00', 'Rule added': 'disabled'}):
            # Send request, verify response
            response = parse_command('192.168.1.123', ['add_rule', 'device2', '10:00', 'disabled'])
            self.assertEqual(response, {'time': '10:00', 'Rule added': 'disabled'})

    def test_add_rule_keyword(self):
        # Mock request to return expected response
        with patch('api_endpoints.request', return_value={'time': 'sunrise', 'Rule added': 'disabled'}), \
             patch('api_endpoints.get_schedule_keywords_dict', return_value=mock_cli_config['schedule_keywords']):

            # Send request, verify response
            response = parse_command('192.168.1.123', ['add_rule', 'device2', 'sunrise', 'disabled'])
            self.assertEqual(response, {'time': 'sunrise', 'Rule added': 'disabled'})

    def test_remove_rule(self):
        # Mock request to return expected response
        with patch('api_endpoints.request', return_value={'Deleted': '10:00'}):
            # Send request, verify response
            response = parse_command('192.168.1.123', ['remove_rule', 'device2', '10:00'])
            self.assertEqual(response, {'Deleted': '10:00'})

    def test_remove_rule_keyword(self):
        # Mock request to return expected response
        with patch('api_endpoints.request', return_value={'Deleted': 'sunrise'}), \
             patch('api_endpoints.get_schedule_keywords_dict', return_value=mock_cli_config['schedule_keywords']):

            # Send request, verify response
            response = parse_command('192.168.1.123', ['remove_rule', 'device2', 'sunrise'])
            self.assertEqual(response, {'Deleted': 'sunrise'})

    def test_save_rules(self):
        # Mock request to return expected response
        with patch('api_endpoints.request', return_value={'Success': 'Rules written to disk'}):
            # Send request, verify response
            response = parse_command('192.168.1.123', ['save_rules'])
            self.assertEqual(response, {'Success': 'Rules written to disk'})

    def test_get_keywords(self):
        # Mock request to return expected response
        with patch('api_endpoints.request', return_value={"sunrise": "05:55", "sunset": "20:20"}):
            # Send request, verify response
            response = parse_command('192.168.1.123', ['get_schedule_keywords'])
            self.assertEqual(response, {"sunrise": "05:55", "sunset": "20:20"})

    def test_add_keyword(self):
        # Mock request to return expected response
        with patch('api_endpoints.request', return_value={"Keyword added": "test", "time": "05:00"}):
            # Send request, verify response
            response = parse_command('192.168.1.123', ['add_schedule_keyword', 'test', '05:00'])
            self.assertEqual(response, {"Keyword added": "test", "time": "05:00"})

    def test_remove_keyword(self):
        # Mock request to return expected response
        with patch('api_endpoints.request', return_value={"Keyword removed": "test"}):
            # Send request, verify response
            response = parse_command('192.168.1.123', ['remove_schedule_keyword', 'test'])
            self.assertEqual(response, {"Keyword removed": "test"})

    def test_save_keywords(self):
        # Mock request to return expected response
        with patch('api_endpoints.request', return_value={"Success": "Keywords written to disk"}):
            # Send request, verify response
            response = parse_command('192.168.1.123', ['save_schedule_keywords'])
            self.assertEqual(response, {"Success": "Keywords written to disk"})

    # Original bug: Timestamp regex allowed both H:MM and HH:MM, should only allow HH:MM
    def test_regression_single_digit_hour(self):
        # Mock request to return expected response (should not run)
        with patch('api_endpoints.request', return_value={"Keyword added": "test", "time": "5:00"}):
            # Send request, should receive error instead of mock response
            response = parse_command('192.168.1.123', ['add_schedule_keyword', 'test', '5:00'])
            self.assertEqual(response, {"ERROR": "Timestamp format must be HH:MM (no AM/PM)"})

    def test_get_attributes(self):
        attributes = {
            'min_rule': 0,
            'nickname': 'Cabinet Lights',
            'bright': 0,
            'scheduled_rule': 'disabled',
            'current_rule': 'disabled',
            'default_rule': 1023,
            'enabled': False,
            'rule_queue': [
                "1023",
                "fade/256/7140",
                "fade/32/7200",
                "Disabled",
                "1023",
                "fade/256/7140"
            ],
            'state': False,
            'name': 'device1',
            'triggered_by': ['sensor1'],
            'max_rule': 1023,
            '_type': 'pwm',
            'group': 'group1',
            'fading': False
        }

        # Mock request to return expected response
        with patch('api_endpoints.request', return_value=attributes):
            # Send request, verify response
            response = parse_command('192.168.1.123', ['get_attributes', 'device2'])
            self.assertEqual(response, attributes)

    def test_ir_key(self):
        # Mock request to return expected response
        with patch('api_endpoints.request', return_value={'tv': 'power'}):
            # Send request, verify response
            response = parse_command('192.168.1.123', ['ir', 'tv', 'power'])
            self.assertEqual(response, {'tv': 'power'})

    def test_ir_get_existing_macros(self):
        # Mock request to return expected response
        with patch('api_endpoints.request', return_value={}):
            # Send request, verify response
            response = parse_command('192.168.1.123', ['ir_get_existing_macros'])
            self.assertEqual(response, {})

    def test_ir_create_macro(self):
        # Mock request to return expected response
        with patch('api_endpoints.request', return_value={"Macro created": 'test1'}):
            # Send request, verify response
            response = parse_command('192.168.1.123', ['ir_create_macro', 'test1'])
            self.assertEqual(response, {"Macro created": 'test1'})

    def test_ir_delete_macro(self):
        # Mock request to return expected response
        with patch('api_endpoints.request', return_value={"Macro deleted": 'test1'}):
            # Send request, verify response
            response = parse_command('192.168.1.123', ['ir_delete_macro', 'test1'])
            self.assertEqual(response, {"Macro deleted": 'test1'})

    def test_ir_save_macros(self):
        # Mock request to return expected response
        with patch('api_endpoints.request', return_value={"Success": "Macros written to disk"}):
            # Send request, verify response
            response = parse_command('192.168.1.123', ['ir_save_macros'])
            self.assertEqual(response, {"Success": "Macros written to disk"})

    def test_ir_add_macro_action(self):
        # Mock request to return expected response
        with patch('api_endpoints.request', return_value={"Macro action added": ['test1', 'tv', 'power']}):
            # Send request, verify response
            response = parse_command('192.168.1.123', ['ir_add_macro_action', 'test1', 'tv', 'power'])
            self.assertEqual(response, {"Macro action added": ['test1', 'tv', 'power']})

    def test_ir_run_macro(self):
        # Mock request to return expected response
        with patch('api_endpoints.request', return_value={"Ran macro": "test1"}):
            # Send request, verify response
            response = parse_command('192.168.1.123', ['ir_run_macro', 'test1', 'tv', 'power'])
            self.assertEqual(response, {"Ran macro": "test1"})

    def test_get_temp(self):
        # Mock request to return expected response
        with patch('api_endpoints.request', return_value={'Temp': 69.9683}):
            # Send request, verify response
            response = parse_command('192.168.1.123', ['get_temp'])
            self.assertEqual(response, {'Temp': 69.9683})

    def test_get_humid(self):
        # Mock request to return expected response
        with patch('api_endpoints.request', return_value={'Humidity': 47.09677}):
            # Send request, verify response
            response = parse_command('192.168.1.123', ['get_humid'])
            self.assertEqual(response, {'Humidity': 47.09677})

    def test_get_climate(self):
        # Mock request to return expected response
        with patch('api_endpoints.request', return_value={'humid': 47.12729, 'temp': 69.94899}):
            # Send request, verify response
            response = parse_command('192.168.1.123', ['get_climate'])
            self.assertEqual(response, {'humid': 47.12729, 'temp': 69.94899})

    def test_clear_log(self):
        # Mock request to return expected response
        with patch('api_endpoints.request', return_value={'clear_log': 'success'}):
            # Send request, verify response
            response = parse_command('192.168.1.123', ['clear_log'])
            self.assertEqual(response, {'clear_log': 'success'})

    def test_condition_met(self):
        # Mock request to return expected response
        with patch('api_endpoints.request', return_value={'Condition': False}):
            # Send request, verify response
            response = parse_command('192.168.1.123', ['condition_met', 'sensor1'])
            self.assertEqual(response, {'Condition': False})

    def test_trigger_sensor(self):
        # Mock request to return expected response
        with patch('api_endpoints.request', return_value={'Triggered': 'sensor1'}):
            # Send request, verify response
            response = parse_command('192.168.1.123', ['trigger_sensor', 'sensor1'])
            self.assertEqual(response, {'Triggered': 'sensor1'})

    def test_turn_on(self):
        # Mock request to return expected response
        with patch('api_endpoints.request', return_value={'On': 'device2'}):
            # Send request, verify response
            response = parse_command('192.168.1.123', ['turn_on', 'device2'])
            self.assertEqual(response, {'On': 'device2'})

    def test_turn_off(self):
        # Mock request to return expected response
        with patch('api_endpoints.request', return_value={'Off': 'device2'}):
            # Send request, verify response
            response = parse_command('192.168.1.123', ['turn_off', 'device2'])
            self.assertEqual(response, {'Off': 'device2'})

    def test_set_gps_coords(self):
        # Mock request to return expected response
        with patch('api_endpoints.request', return_value={"Success": "GPS coordinates set"}):
            # Send request, verify response
            response = parse_command('192.168.1.123', ['set_gps_coords', '-90', '0.1'])
            self.assertEqual(response, {"Success": "GPS coordinates set"})


# Confirm that correct errors are shown when endpoint arguments are omitted/incorrect
class TestEndpointErrors(TestCase):

    def test_disable_invalid_arg(self):
        # Send request, verify response
        response = parse_command('192.168.1.123', ['disable', 'not-a-device'])
        self.assertEqual(response, {"ERROR": "Can only disable devices and sensors"})

    def test_enable_invalid_arg(self):
        # Send request, verify response
        response = parse_command('192.168.1.123', ['enable', 'not-a-device'])
        self.assertEqual(response, {"ERROR": "Can only enable devices and sensors"})

    def test_disable_in_invalid_arg(self):
        # Send request, verify response
        response = parse_command('192.168.1.123', ['disable_in', 'not-a-device'])
        self.assertEqual(response, {"ERROR": "Can only disable devices and sensors"})

    def test_disable_in_no_delay_arg(self):
        # Send request, verify response
        response = parse_command('192.168.1.123', ['disable_in', 'device1'])
        self.assertEqual(response, {"ERROR": "Please specify delay in minutes"})

    def test_enable_in_invalid_arg(self):
        # Send request, verify response
        response = parse_command('192.168.1.123', ['enable_in', 'not-a-device'])
        self.assertEqual(response, {"ERROR": "Can only enable devices and sensors"})

    def test_enable_in_no_delay_arg(self):
        # Send request, verify response
        response = parse_command('192.168.1.123', ['enable_in', 'device1'])
        self.assertEqual(response, {"ERROR": "Please specify delay in minutes"})

    def test_set_rule_invalid_arg(self):
        # Send request, verify response
        response = parse_command('192.168.1.123', ['set_rule', 'not-a-device'])
        self.assertEqual(response, {"ERROR": "Can only set rules for devices and sensors"})

    def test_set_rule_no_delay_arg(self):
        # Send request, verify response
        response = parse_command('192.168.1.123', ['set_rule', 'device1'])
        self.assertEqual(response, {"ERROR": "Must specify new rule"})

    def test_increment_rule_invalid_target(self):
        # Send request, verify response
        response = parse_command('192.168.1.123', ['increment_rule', 'ir_blaster', '50'])
        self.assertEqual(response, {"ERROR": "Target must be device or sensor with int rule"})

    def test_increment_rule_no_amount_arg(self):
        # Send request, verify response
        response = parse_command('192.168.1.123', ['increment_rule', 'device1'])
        self.assertEqual(response, {"ERROR": "Must specify amount (int) to increment by"})

    def test_reset_rule_invalid_arg(self):
        # Send request, verify response
        response = parse_command('192.168.1.123', ['reset_rule', 'not-a-device'])
        self.assertEqual(response, {"ERROR": "Can only set rules for devices and sensors"})

    def test_get_schedule_rules_invalid_arg(self):
        # Send request, verify response
        response = parse_command('192.168.1.123', ['get_schedule_rules', 'not-a-device'])
        self.assertEqual(response, {"ERROR": "Only devices and sensors have schedule rules"})

    def test_add_rule_invalid_arg(self):
        # Send request, verify response
        response = parse_command('192.168.1.123', ['add_rule', 'not-a-device'])
        self.assertEqual(response, {"ERROR": "Only devices and sensors have schedule rules"})

    def test_add_rule_no_time_arg(self):
        # Send request, verify response
        response = parse_command('192.168.1.123', ['add_rule', 'device1'])
        self.assertEqual(response, {"ERROR": "Must specify timestamp (HH:MM) or keyword followed by rule"})

    def test_add_rule_no_rule_arg(self):
        # Send request, verify response
        response = parse_command('192.168.1.123', ['add_rule', 'device1', '01:30'])
        self.assertEqual(response, {"ERROR": "Must specify new rule"})

    def test_add_rule_keyword_no_config_file(self):
        # Attempt to use keyword while simulating missing schedule-keywords.json
        with patch("builtins.open", MagicMock(side_effect=FileNotFoundError)):
            response = parse_command('192.168.1.123', ['add_rule', 'device1', 'sunrise', '50'])
            self.assertEqual(response, {"ERROR": "Must specify timestamp (HH:MM) or keyword followed by rule"})

    def test_remove_rule_invalid_arg(self):
        # Send request, verify response
        response = parse_command('192.168.1.123', ['remove_rule', 'not-a-device'])
        self.assertEqual(response, {"ERROR": "Only devices and sensors have schedule rules"})

    def test_remove_rule_no_time_arg(self):
        # Send request, verify response
        response = parse_command('192.168.1.123', ['remove_rule', 'device1'])
        self.assertEqual(response, {"ERROR": "Must specify timestamp (HH:MM) or keyword of rule to remove"})

    def test_get_attributes_invalid_arg(self):
        # Send request, verify response
        response = parse_command('192.168.1.123', ['get_attributes', 'not-a-device'])
        self.assertEqual(response, {"ERROR": "Must specify device or sensor"})

    def test_condition_met_invalid_arg(self):
        # Send request, verify response
        response = parse_command('192.168.1.123', ['condition_met', 'device1'])
        self.assertEqual(response, {"ERROR": "Must specify sensor"})

    def test_trigger_sensor_invalid_arg(self):
        # Send request, verify response
        response = parse_command('192.168.1.123', ['trigger_sensor', 'device1'])
        self.assertEqual(response, {"ERROR": "Must specify sensor"})

    def test_turn_on_invalid_arg(self):
        # Send request, verify response
        response = parse_command('192.168.1.123', ['turn_on', 'sensor1'])
        self.assertEqual(response, {"ERROR": "Can only turn on/off devices, use enable/disable for sensors"})

    def test_turn_off_invalid_arg(self):
        # Send request, verify response
        response = parse_command('192.168.1.123', ['turn_off', 'sensor1'])
        self.assertEqual(response, {"ERROR": "Can only turn on/off devices, use enable/disable for sensors"})

    def test_ir_no_key(self):
        # Send request, verify response
        response = parse_command('192.168.1.123', ['ir', 'tv'])
        self.assertEqual(response, {"ERROR": f"Must specify one of the following commands: {ir_commands['tv']}"})

        response = parse_command('192.168.1.123', ['ir', 'ac'])
        self.assertEqual(response, {"ERROR": f"Must specify one of the following commands: {ir_commands['ac']}"})

    def test_ir_invalid_target(self):
        response = parse_command('192.168.1.123', ['ir', 'pacemaker'])
        self.assertEqual(response, {"Example usage": "./api_client.py ir [tv|ac] [command]"})

    def test_ir_add_macro_action_missing_args(self):
        response = parse_command('192.168.1.123', ['ir_add_macro_action', 'test1'])
        self.assertEqual(
            response,
            {"Example usage": "./api_client.py ir_add_macro_action [name] [target] [key] <delay> <repeats>"}
        )

    def test_set_gps_coords_missing_args(self):
        response = parse_command('192.168.1.123', ['set_gps_coords', '-90'])
        self.assertEqual(response, {"Example usage": "./api_client.py set_gps_coords [latitude] [longitude]"})

    # Original bug: Timestamp regex allowed both H:MM and HH:MM, should only allow HH:MM
    def test_regression_single_digit_hour(self):
        # Mock request to return expected response (should not run)
        with patch('api_endpoints.request', return_value={'time': '5:00', 'Rule added': 'disabled'}):
            # Send request, should receive error instead of mock response
            response = parse_command('192.168.1.123', ['add_rule', 'device2', '5:00', 'disabled'])
            self.assertEqual(response, {"ERROR": "Must specify timestamp (HH:MM) or keyword followed by rule"})

        # Mock request to return expected response (should not run)
        with patch('api_endpoints.request', return_value={'Deleted': '5:00'}):
            # Send request, verify response
            response = parse_command('192.168.1.123', ['remove_rule', 'device2', '5:00'])
            self.assertEqual(response, {"ERROR": "Must specify timestamp (HH:MM) or keyword of rule to remove"})

    # Original bug: Delay argument for enable_in, disable_in was cast to float with no
    # error handling, leading to uncaught exception when an invalid argument was given.
    def test_regression_enable_in_disable_in_invalid_delay(self):
        # Confirm correct error for string delay, confirm request not called
        with patch('api_endpoints.request') as mock_request:
            response = parse_command('192.168.1.123', ['enable_in', 'device1', 'string'])
            self.assertEqual(response, {"ERROR": "Delay argument must be int or float"})
            self.assertFalse(mock_request.called)

        # Confirm correct error for NaN delay, confirm request not called
        with patch('api_endpoints.request') as mock_request:
            response = parse_command('192.168.1.123', ['enable_in', 'device1', 'NaN'])
            self.assertEqual(response, {"ERROR": "Delay argument must be int or float"})
            self.assertFalse(mock_request.called)

        # Repeat NaN delay for disable_in, confirm error + request not called
        with patch('api_endpoints.request') as mock_request:
            response = parse_command('192.168.1.123', ['disable_in', 'device1', 'NaN'])
            self.assertEqual(response, {"ERROR": "Delay argument must be int or float"})
            self.assertFalse(mock_request.called)


# Test CLI script entrypoint
class TestMain(TestCase):
    def test_main(self):
        # Redirect stdout to variable
        stdout = StringIO()
        sys.stdout = stdout

        # Mock sys.arg to simulate running from command line
        with patch("sys.argv", ["api_client.py", "192.168.1.123", "enable", "device1"]), \
             patch('api_client.nodes', mock_cli_config['nodes']), \
             patch('api_endpoints.request', return_value={'Enabled': 'device1'}):

            # Run main, verify response printed to console
            main()
            self.assertEqual(json.loads(stdout.getvalue()), {'Enabled': 'device1'})

        # Reset stdout
        sys.stdout = sys.__stdout__
