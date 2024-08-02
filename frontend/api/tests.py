import json
import asyncio
from copy import deepcopy
from unittest.mock import patch, MagicMock, AsyncMock, call
from django.test import TestCase
from .views import parse_command
from api_endpoints import request
from .unit_test_helpers import (
    instance_metadata,
    config1_status,
    config2_status,
    config2_api_target_options,
    config2_ir_macros,
    config2_existing_macros
)
from node_configuration.models import ScheduleKeyword, Node
from node_configuration.unit_test_helpers import (
    create_test_nodes,
    JSONClient,
    test_config_1
)
from Webrepl import Webrepl


# Test function that makes async API calls to esp32 nodes (called by send_command)
class RequestTests(TestCase):
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
             patch('api.views.json.loads', side_effect=ValueError):

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
            response = await asyncio.wait_for(
                request('192.168.1.123', ['enable', 'device1']),
                timeout=6
            )
            self.assertEqual(response, "Error: Timed out waiting for response")


# Test send_command function that bridges frontend HTTP requests to esp32 API calls
class SendCommandTests(TestCase):
    def setUp(self):
        # Set default content_type for post requests (avoid long lines)
        self.client = JSONClient()

    def test_send_command(self):
        payload = {"command": "turn_off", "instance": "device1", "target": "192.168.1.123"}

        # Mock parse_command to do nothing
        with patch('api.views.parse_command', return_value={"On": "device1"}) as mock_parse_command:
            # Make API call, confirm response, confirm parse_command called once
            response = self.client.post('/send_command', payload)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()['message'], {"On": "device1"})
            self.assertEqual(mock_parse_command.call_count, 1)

    def test_send_command_with_extra_whitespace(self):
        # Mock parse_command to check args
        with patch('api.views.parse_command', return_value='mock') as mock_parse_command:
            # Create payload with extra whitespace around target instance
            payload = {
                "command": "set_rule",
                "instance": "   device1 ",
                "target": "192.168.1.123",
                "rule": 50
            }
            self.client.post('/send_command', payload)

            # Confirm extra whitespace was removed, int rule was not modified
            self.assertEqual(
                mock_parse_command.call_args_list[0],
                call('192.168.1.123', ['set_rule', 'device1', 50])
            )

    def test_send_command_containing_dict(self):
        # Mock parse_command to check args
        with patch('api.views.parse_command', return_value='mock') as mock_parse_command:
            # Simulate user setting api-target rule
            payload = {
                "command": "set_rule",
                "instance": "device1",
                "target": "192.168.1.123",
                "rule": {
                    "on": ["turn_on", "device1"],
                    "off": ["turn_off", "device1"]
                }
            }
            self.client.post('/send_command', payload)

            # Confirm dict rule was stringified (node can't receive objects over API)
            self.assertEqual(
                mock_parse_command.call_args_list[0],
                call(
                    '192.168.1.123',
                    [
                        'set_rule',
                        'device1',
                        '{"on": ["turn_on", "device1"], "off": ["turn_off", "device1"]}'
                    ]
                )
            )

    def test_send_command_invalid_method(self):
        # Make get request (requires post)
        response = self.client.get('/send_command')
        self.assertEqual(response.status_code, 405)
        self.assertEqual(response.json()['message'], 'Must post data')

    def test_send_command_connection_failed(self):
        payload = {"command": "turn_off", "instance": "device1", "target": "192.168.1.123"}

        # Mock parse_command to simulate failed connection to node
        with patch('api.views.parse_command', side_effect=OSError) as mock_parse_command:
            # Make API call, confirm response, confirm parse_command called once
            response = self.client.post('/send_command', payload)
            self.assertEqual(response.status_code, 502)
            self.assertEqual(response.json()['message'], "Unable to connect")
            self.assertEqual(mock_parse_command.call_count, 1)


# Test API Card interface
class ApiCardTests(TestCase):
    def setUp(self):
        # Create 3 test nodes
        create_test_nodes()

    def test_get_status(self):
        # Mock request to return status object
        with patch('api_endpoints.request', return_value=config1_status):
            response = self.client.get('/get_status/Test1')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()['message'], config1_status)

    def test_get_status_offline(self):
        # Mock request to simulate offline target node
        with patch('api_endpoints.request', side_effect=OSError("Unable to connect")):
            response = self.client.get('/get_status/Test1')
            self.assertEqual(response.status_code, 502)
            self.assertEqual(response.json()['message'], "Unable to connect")

    def test_get_status_time_out(self):
        # Mock request to simulate network connection time out
        with patch('api_endpoints.request', return_value="Error: Request timed out"):
            response = self.client.get('/get_status/Test1')
            self.assertEqual(response.status_code, 502)
            self.assertEqual(response.json()['message'], "Error: Request timed out")

    def test_get_status_does_not_exist(self):
        response = self.client.get('/get_status/Fake_Name')
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()['message'], 'Node named Fake_Name not found')

    def test_api_frontend(self):
        # Mock request to return the expected status object
        with patch('api_endpoints.request', return_value=config1_status):
            # Request page, confirm correct template used
            response = self.client.get('/api/Test1')
            self.assertEqual(response.status_code, 200)
            self.assertTemplateUsed(response, 'api/api_card.html')

            # Confirm context contains status object, target IP, and metadata
            self.assertEqual(response.context['status'], config1_status)
            self.assertEqual(response.context['target_ip'], '192.168.1.123')
            self.assertEqual(response.context['instance_metadata'], instance_metadata)

            # Confirm not recording macro
            self.assertFalse(response.context['recording'])

            # Confirm no api_target_options or ir_macros contexts
            self.assertFalse('api_target_options' in response.context.keys())
            self.assertFalse('ir_macros' in response.context.keys())

    # Repeat test above with a node containing ApiTarget and Thermostat
    def test_api_target_and_thermostat(self):
        # Mock request to return the expected status object followed by existing_macros object
        with patch('api_endpoints.request', side_effect=[config2_status, config2_existing_macros]):
            # Request page, confirm correct template used
            response = self.client.get('/api/Test2')
            self.assertEqual(response.status_code, 200)
            self.assertTemplateUsed(response, 'api/api_card.html')

            # Confirm context contains status object, target IP, and metadata
            self.assertEqual(response.context['status'], config2_status)
            self.assertEqual(response.context['target_ip'], '192.168.1.124')
            self.assertEqual(response.context['instance_metadata'], instance_metadata)

            # Confirm not recording macro
            self.assertFalse(response.context['recording'])

            # Confirm expected api_target_options and ir_macros contexts
            self.assertEqual(response.context['api_target_options'], config2_api_target_options)
            self.assertEqual(response.context['ir_macros'], config2_ir_macros)

    def test_failed_connection(self):
        # Mock request to simulate offline target node
        with patch('api_endpoints.request', side_effect=OSError("Unable to connect")):
            # Request page, confirm unable_to_connect template used
            response = self.client.get('/api/Test1')
            self.assertEqual(response.status_code, 200)
            self.assertTemplateUsed(response, 'api/unable_to_connect.html')

            # Confirm context
            self.assertEqual(
                response.context['context'],
                {'ip': '192.168.1.123', 'id': 'Test1'}
            )

        # Mock parse_command to simulate timed out request
        with patch('api_endpoints.request', return_value='Error: Request timed out'):
            # Request page, confirm correct template used
            response = self.client.get('/api/Test1')
            self.assertEqual(response.status_code, 200)
            self.assertTemplateUsed(response, 'api/unable_to_connect.html')

        # Mock parse_command to simulate crashed node
        with patch('api_endpoints.request', return_value='Error: Failed to connect'):
            # Request page, confirm correct template used
            response = self.client.get('/api/Test1')
            self.assertEqual(response.status_code, 200)
            self.assertTemplateUsed(response, 'api/unable_to_connect.html')

    def test_recording_mode(self):
        # Mock request to return the expected status object
        with patch('api_endpoints.request', return_value=config1_status):
            # Request page, confirm correct template used
            response = self.client.get('/api/Test1/macro-name')
            self.assertEqual(response.status_code, 200)
            self.assertTemplateUsed(response, 'api/api_card.html')

            # Confirm context contains macro name
            self.assertEqual(response.context['recording'], 'macro-name')

    def test_node_does_not_exist(self):
        # Request page, confirm correct template used
        response = self.client.get('/api/fake-node')
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()['message'], 'Node named fake-node not found')

    # Original issue: View only caught errors while opening connection to the node,
    # but did not handle situations where connection was successful and an error
    # occurred during the request (timeout waiting for response etc).
    # Now traps all by checking if response starts with "Error: "
    def test_regression_fails_to_show_unable_to_connect_page(self):
        # Mock parse_command to simulate slow response
        with patch('api_endpoints.request', return_value='Error: Timed out waiting for response'):
            # Request page, confirm correct template used
            response = self.client.get('/api/Test1')
            self.assertEqual(response.status_code, 200)
            self.assertTemplateUsed(response, 'api/unable_to_connect.html')

        # Mock parse_command to simulate error on node
        with patch('api_endpoints.request', return_value='Error: Request failed'):
            # Request page, confirm correct template used
            response = self.client.get('/api/Test1')
            self.assertEqual(response.status_code, 200)
            self.assertTemplateUsed(response, 'api/unable_to_connect.html')

        # Mock parse_command to simulate invalid response object
        with patch('api_endpoints.request', return_value='Error: Unable to decode response'):
            # Request page, confirm correct template used
            response = self.client.get('/api/Test1')
            self.assertEqual(response.status_code, 200)
            self.assertTemplateUsed(response, 'api/unable_to_connect.html')


# Test endpoints used to manage schedule keywords
class ScheduleKeywordTests(TestCase):
    def setUp(self):
        # Create 3 test nodes
        create_test_nodes()

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

    def test_add_errors(self):
        # Send request with no args, verify error
        response = parse_command('192.168.1.123', ['add_schedule_keyword'])
        self.assertEqual(response, 'Error: Missing required parameters')

        # Send request with no timestamp, verify error
        response = parse_command('192.168.1.123', ['add_schedule_keyword', 'test'])
        self.assertEqual(response, {"ERROR": "Timestamp format must be HH:MM (no AM/PM)"})

    def test_remove_errors(self):
        # Send request with no args, verify error
        response = parse_command('192.168.1.123', ['remove_schedule_keyword'])
        self.assertEqual(response, 'Error: Missing required parameters')

    # Original bug: Timestamp regex allowed both H:MM and HH:MM, should only allow HH:MM
    def test_regression_single_digit_hour(self):
        # Mock request to return expected response (should not run)
        with patch('api_endpoints.request', return_value={"Keyword added": "test", "time": "5:00"}):
            # Send request, should receive error instead of mock response
            response = parse_command('192.168.1.123', ['add_schedule_keyword', 'test', '5:00'])
            self.assertEqual(response, {"ERROR": "Timestamp format must be HH:MM (no AM/PM)"})


class SyncScheduleKeywordTests(TestCase):
    def setUp(self):
        # Set default content_type for post requests (avoid long lines)
        self.client = JSONClient()

        # Create 3 test nodes
        create_test_nodes()

        # Create 3 test keywords, confirm 5 total (sunrise + sunset already exist)
        ScheduleKeyword.objects.create(keyword='Test1', timestamp='12:34')
        ScheduleKeyword.objects.create(keyword='Test2', timestamp='23:45')
        ScheduleKeyword.objects.create(keyword='Test3', timestamp='04:56')
        self.assertEqual(len(ScheduleKeyword.objects.all()), 5)

        # Simulated request from node that already has all keywords
        self.payload = {
            'ip': '192.168.1.123',
            'existing_keywords': {
                'sunrise': '06:00',
                'sunset': '18:00',
                'Test1': '12:34',
                'Test2': '23:45',
                'Test3': '04:56'
            }
        }

    def test_sync_keywords(self):
        # Mock parse_command to do nothing
        with patch('api.views.parse_command', return_value="Done") as mock_parse_command:
            # Send request, verify response
            response = self.client.post('/sync_schedule_keywords', self.payload)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()['message'], "Done")

            # Should not be called, no keywords to upload
            self.assertFalse(mock_parse_command.called)

        # Delete 2 keywords, test again
        del self.payload['existing_keywords']['Test1']
        del self.payload['existing_keywords']['sunset']

        with patch('api.views.parse_command', return_value="Done") as mock_parse_command:
            response = self.client.post('/sync_schedule_keywords', self.payload)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()['message'], "Done")

            # Should be called 3 times: add 2 missing keywords, save
            self.assertEqual(mock_parse_command.call_count, 3)
            self.assertEqual(
                mock_parse_command.call_args_list,
                [
                    call('192.168.1.123', ['add_schedule_keyword', 'sunset', '18:00']),
                    call('192.168.1.123', ['add_schedule_keyword', 'Test1', '12:34']),
                    call('192.168.1.123', ['save_schedule_keywords'])
                ]
            )

            # Delete all keywords, test again
            self.payload['existing_keywords'] = {}
            mock_parse_command.reset_mock()

            response = self.client.post('/sync_schedule_keywords', self.payload)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()['message'], "Done")

            # Should be called 6 times: add 5 missing keywords, save
            self.assertEqual(mock_parse_command.call_count, 6)
            self.assertEqual(
                mock_parse_command.call_args_list,
                [
                    call('192.168.1.123', ['add_schedule_keyword', 'sunrise', '06:00']),
                    call('192.168.1.123', ['add_schedule_keyword', 'sunset', '18:00']),
                    call('192.168.1.123', ['add_schedule_keyword', 'Test1', '12:34']),
                    call('192.168.1.123', ['add_schedule_keyword', 'Test2', '23:45']),
                    call('192.168.1.123', ['add_schedule_keyword', 'Test3', '04:56']),
                    call('192.168.1.123', ['save_schedule_keywords'])
                ]
            )

    def test_sync_keywords_update_timestamp(self):
        # Change keyword timestamp
        self.payload['existing_keywords']['Test1'] = '10:00'
        self.payload['existing_keywords']['Test3'] = '20:00'

        # Mock parse_command to do nothing
        with patch('api.views.parse_command', return_value="Done") as mock_parse_command:
            # Send request, verify response
            response = self.client.post('/sync_schedule_keywords', self.payload)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()['message'], "Done")

            # Should be called 3 times: overwrite each keyword, save
            self.assertEqual(mock_parse_command.call_count, 3)
            self.assertEqual(
                mock_parse_command.call_args_list,
                [
                    call('192.168.1.123', ['add_schedule_keyword', 'Test1', '12:34']),
                    call('192.168.1.123', ['add_schedule_keyword', 'Test3', '04:56']),
                    call('192.168.1.123', ['save_schedule_keywords'])
                ]
            )

    def test_sync_keywords_update_keyword(self):
        # Change keyword without changing timestamp
        self.payload['existing_keywords']['New'] = '12:34'
        del self.payload['existing_keywords']['Test1']

        # Mock parse_command to do nothing
        with patch('api.views.parse_command', return_value="Done") as mock_parse_command:
            # Send request, verify response
            response = self.client.post('/sync_schedule_keywords', self.payload)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()['message'], "Done")

            # Should be called 3 times: Add new keyword, delete old keyword, save
            self.assertEqual(mock_parse_command.call_count, 3)
            self.assertEqual(
                mock_parse_command.call_args_list,
                [
                    call('192.168.1.123', ['add_schedule_keyword', 'Test1', '12:34']),
                    call('192.168.1.123', ['remove_schedule_keyword', 'New']),
                    call('192.168.1.123', ['save_schedule_keywords'])
                ]
            )

    def test_sync_keywords_delete(self):
        # Delete all keywords except sunrise/sunset
        ScheduleKeyword.objects.get(keyword='Test1').delete()
        ScheduleKeyword.objects.get(keyword='Test2').delete()
        ScheduleKeyword.objects.get(keyword='Test3').delete()

        # Mock parse_command to do nothing
        with patch('api.views.parse_command', return_value="Done") as mock_parse_command:
            # Send request for Node with all 5, should delete same keywords deleted above
            response = self.client.post('/sync_schedule_keywords', self.payload)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()['message'], "Done")

            # Should be called 4 times: Delete 3 keywords no longer in database, save
            self.assertEqual(mock_parse_command.call_count, 4)
            self.assertEqual(
                mock_parse_command.call_args_list,
                [
                    call('192.168.1.123', ['remove_schedule_keyword', 'Test1']),
                    call('192.168.1.123', ['remove_schedule_keyword', 'Test2']),
                    call('192.168.1.123', ['remove_schedule_keyword', 'Test3']),
                    call('192.168.1.123', ['save_schedule_keywords'])
                ]
            )

    def test_sync_keywords_errors(self):
        # Make invalid get request (requires post), confirm error
        response = self.client.get('/sync_schedule_keywords')
        self.assertEqual(response.status_code, 405)
        self.assertEqual(response.json()['message'], 'Must post data')


# Test endpoint that syncs config file from node to database when user modifies schedule rules
class SyncScheduleRulesTests(TestCase):
    def setUp(self):
        # Set default content_type for post requests (avoid long lines)
        self.client = JSONClient()

        # Create 3 test nodes
        create_test_nodes()
        self.node = Node.objects.get(ip='192.168.1.123')

    def test_sync_schedule_rules(self):
        # Confirm node config is unmodified
        self.assertEqual(self.node.config.config, test_config_1)

        # Create modified config, convert to format returned by Webrepl.get_file_mem
        mock_config = deepcopy(test_config_1)
        del mock_config['device1']['schedule']['05:00']
        encoded_mock_config = json.dumps(mock_config).encode()

        # Mock Webrepl.get_file_mem to return the modified config
        # Mock parse_command to return expected response for save_rules endpoint
        with patch.object(Webrepl, 'open_connection', return_value=True) as mock_open_connection, \
             patch.object(Webrepl, 'get_file_mem', return_value=encoded_mock_config) as mock_get_file, \
             patch('api.views.parse_command', return_value={"Success": "Rules written to disk"}):

            # Send request, verify response + function calls
            response = self.client.post('/sync_schedule_rules', {"ip": '192.168.1.123'})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()['message'], "Done syncing schedule rules")
            self.assertTrue(mock_open_connection.called)
            self.assertTrue(mock_get_file.called_with('config.json'))

            # Verify that node config was replaced with the modified config
            self.node.refresh_from_db()
            self.assertEqual(self.node.config.config, mock_config)

    def test_invalid_get_request(self):
        # Send get request (requires post), verify error
        response = self.client.get('/sync_schedule_rules')
        self.assertEqual(response.status_code, 405)
        self.assertEqual(response.json()['message'], 'Must post data')

    def test_invalid_node(self):
        # Send request with IP that does not exist in database, verify error
        response = self.client.post('/sync_schedule_rules', {"ip": '192.168.1.100'})
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()['message'], 'Node with IP 192.168.1.100 not found')

    def test_failed_to_save_rules(self):
        # Mock parse_command to return request timeout error
        with patch('api.views.parse_command', return_value="Error: Request timed out"):
            # Send request, verify error
            response = self.client.post('/sync_schedule_rules', {"ip": '192.168.1.123'})
            self.assertEqual(response.status_code, 500)
            self.assertEqual(response.json()['message'], 'Failed to save rules')


# Test endpoints used to create and modify IR macros
class IrMacroTests(TestCase):
    def setUp(self):
        # Set default content_type for post requests (avoid long lines)
        self.client = JSONClient()

    def test_edit_ir_macro(self):
        # Simulated payload from frontend
        payload = {
            'ip': '192.168.1.123',
            'name': 'backlight_on',
            'actions': [
                'tv settings 1500 1',
                'tv right 500 1',
                'tv down 500 1',
                'tv enter 500 1',
                'tv right 150 14',
                'tv exit 0 1'
            ]
        }

        # Mock parse_command to do nothing
        with patch('api.views.parse_command', return_value=None) as mock_parse_command:
            # Make API call, confirm response, confirm parse_command called once
            response = self.client.post('/edit_ir_macro', payload)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()['message'], "Done")

            # Confirm parse_command was called 9 times with correct args
            # Delete old macro, create new macro with same name, add 6 actions, save
            self.assertEqual(mock_parse_command.call_count, 9)
            calls = mock_parse_command.call_args_list
            self.assertEqual(
                calls[0].args,
                ('192.168.1.123', ['ir_delete_macro', 'backlight_on'])
            )
            self.assertEqual(
                calls[1].args,
                ('192.168.1.123', ['ir_create_macro', 'backlight_on'])
            )
            self.assertEqual(
                calls[2].args,
                ('192.168.1.123', ['ir_add_macro_action', 'backlight_on', 'tv', 'settings', '1500', '1'])
            )
            self.assertEqual(
                calls[3].args,
                ('192.168.1.123', ['ir_add_macro_action', 'backlight_on', 'tv', 'right', '500', '1'])
            )
            self.assertEqual(
                calls[4].args,
                ('192.168.1.123', ['ir_add_macro_action', 'backlight_on', 'tv', 'down', '500', '1'])
            )
            self.assertEqual(
                calls[5].args,
                ('192.168.1.123', ['ir_add_macro_action', 'backlight_on', 'tv', 'enter', '500', '1'])
            )
            self.assertEqual(
                calls[6].args,
                ('192.168.1.123', ['ir_add_macro_action', 'backlight_on', 'tv', 'right', '150', '14'])
            )
            self.assertEqual(
                calls[7].args,
                ('192.168.1.123', ['ir_add_macro_action', 'backlight_on', 'tv', 'exit', '0', '1'])
            )
            self.assertEqual(
                calls[8].args,
                ('192.168.1.123', ['ir_save_macros'])
            )

    def test_add_ir_macro(self):
        # Simulated payload from frontend
        payload = {
            'ip': '192.168.1.123',
            'name': 'backlight_on',
            'actions': [
                'tv settings 1500 1',
                'tv right 500 1',
                'tv down 500 1',
                'tv enter 500 1',
                'tv right 150 14',
                'tv exit 0 1'
            ]
        }

        # Mock parse_command to do nothing
        with patch('api.views.parse_command', return_value=None) as mock_parse_command:
            # Make API call, confirm response
            response = self.client.post('/add_ir_macro', payload)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()['message'], "Done")

            # Confirm parse_command was called 8 times with correct args
            # Create new macro, add 6 actions, save
            self.assertEqual(mock_parse_command.call_count, 8)
            calls = mock_parse_command.call_args_list
            self.assertEqual(
                calls[0].args,
                ('192.168.1.123', ['ir_create_macro', 'backlight_on'])
            )
            self.assertEqual(
                calls[1].args,
                ('192.168.1.123', ['ir_add_macro_action', 'backlight_on', 'tv', 'settings', '1500', '1'])
            )
            self.assertEqual(
                calls[2].args,
                ('192.168.1.123', ['ir_add_macro_action', 'backlight_on', 'tv', 'right', '500', '1'])
            )
            self.assertEqual(
                calls[3].args,
                ('192.168.1.123', ['ir_add_macro_action', 'backlight_on', 'tv', 'down', '500', '1'])
            )
            self.assertEqual(
                calls[4].args,
                ('192.168.1.123', ['ir_add_macro_action', 'backlight_on', 'tv', 'enter', '500', '1'])
            )
            self.assertEqual(
                calls[5].args,
                ('192.168.1.123', ['ir_add_macro_action', 'backlight_on', 'tv', 'right', '150', '14'])
            )
            self.assertEqual(
                calls[6].args,
                ('192.168.1.123', ['ir_add_macro_action', 'backlight_on', 'tv', 'exit', '0', '1'])
            )
            self.assertEqual(
                calls[7].args,
                ('192.168.1.123', ['ir_save_macros'])
            )
