import json
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from django.test import TestCase
from django.db import IntegrityError
from .models import Macro
from .views import parse_command, request
from .unit_test_helpers import config1_status_object, config1_api_context, config2_status_object, config2_api_context
from node_configuration.unit_test_helpers import create_test_nodes, clean_up_test_nodes
from node_configuration.models import ScheduleKeyword


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
        with patch('api.views.asyncio.open_connection', side_effect=self.mock_open_connection), \
             patch('api.views.asyncio.wait_for', side_effect=self.mock_wait_for):

            # Send request, verify response
            response = await request('192.168.1.123', ['enable', 'device1'])
            self.assertEqual(response, {'Enabled': 'device1'})

    async def test_request_connection_errors(self):
        # Simulate timed out connection (target node event loop blocked)
        with patch('api.views.asyncio.wait_for', side_effect=asyncio.TimeoutError):

            # Make request, verify error
            response = await request('192.168.1.123', ['enable', 'device1'])
            self.assertEqual(response, "Error: Request timed out")

        # Simulate failed connection (target node offline, wrong IP, etc)
        with patch('api.views.asyncio.wait_for', side_effect=OSError):

            # Make request, verify error
            response = await request('192.168.1.123', ['enable', 'device1'])
            self.assertEqual(response, "Error: Failed to connect")

        # Simulate successful connection, failed write
        with patch('api.views.asyncio.open_connection', side_effect=self.mock_open_connection_fail), \
             patch('api.views.asyncio.wait_for', side_effect=self.mock_wait_for):

            # Make request, verify error
            response = await request('192.168.1.123', ['enable', 'device1'])
            self.assertEqual(response, "Error: Request failed")

        # Simulate successful connection, receive invalid response
        with patch('api.views.asyncio.open_connection', side_effect=self.mock_open_connection), \
             patch('api.views.asyncio.wait_for', side_effect=self.mock_wait_for), \
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
        with patch('api.views.asyncio.open_connection', side_effect=self.mock_open_connection_hang):
            # Send request, verify error
            # Request wrapped in 6 second timeout to prevent hanging in case of failure
            response = await asyncio.wait_for(request('192.168.1.123', ['enable', 'device1']), timeout=6)
            self.assertEqual(response, "Error: Timed out waiting for response")


# Test send_command function that bridges frontend HTTP requests to esp32 API calls
class SendCommandTests(TestCase):

    # Simulate send_command call from new Api frontend
    def test_send_command_api_cards(self):
        payload = {"command": "turn_off", "instance": "device1", "target": "192.168.1.123"}

        # Mock parse_command to do nothing
        with patch('api.views.parse_command', return_value={"On": "device1"}) as mock_parse_command:
            # Make API call, confirm response, confirm parse_command called once
            response = self.client.post('/send_command', payload, content_type='application/json')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json(), {"On": "device1"})
            self.assertEqual(mock_parse_command.call_count, 1)

    # Simulate send_command call from original Api frontend
    def test_send_command_legacy_api(self):
        create_test_nodes()
        payload = {"command": "turn_off", "instance": "device1", "target": "Test1"}

        # Mock parse_command to do nothing
        with patch('api.views.parse_command', return_value={"On": "device1"}) as mock_parse_command:
            # Make API call, confirm response, confirm parse_command called once
            response = self.client.post('/send_command', payload, content_type='application/json')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json(), {"On": "device1"})
            self.assertEqual(mock_parse_command.call_count, 1)

        # Remove test configs from disk
        clean_up_test_nodes()

    def test_send_command_invalid_method(self):
        # Make get request (requires post)
        response = self.client.get('/send_command')
        self.assertEqual(response.status_code, 405)
        self.assertEqual(response.json(), {'Error': 'Must post data'})

    def test_send_command_connection_failed(self):
        payload = {"command": "turn_off", "instance": "device1", "target": "192.168.1.123"}

        # Mock parse_command to simulate failed connection to node
        with patch('api.views.parse_command', side_effect=OSError) as mock_parse_command:
            # Make API call, confirm response, confirm parse_command called once
            response = self.client.post('/send_command', payload, content_type='application/json')
            self.assertEqual(response.status_code, 502)
            self.assertEqual(response.json(), "Error: Unable to connect.")
            self.assertEqual(mock_parse_command.call_count, 1)

    # Test legacy frontend enable_for/disable_for function
    def test_legacy_api_delay_input(self):
        create_test_nodes()
        payload_disable = {'select_target': 'device1', 'delay_input': '5', 'target': 'Test1', 'command': 'disable'}
        payload_enable = {'select_target': 'device1', 'delay_input': '5', 'target': 'Test1', 'command': 'enable'}

        # Mock parse_command to do nothing
        with patch('api.views.parse_command', return_value={'Disabled': 'device1'}) as mock_parse_command:
            # Make API call, confirm response, confirm parse_command called twice
            response = self.client.post('/send_command', payload_disable, content_type='application/json')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json(), {'Disabled': 'device1'})
            self.assertEqual(mock_parse_command.call_count, 2)

        # Mock parse_command to do nothing
        with patch('api.views.parse_command', return_value={'Enabled': 'device1'}) as mock_parse_command:
            # Make API call, confirm response, confirm parse_command called twice
            response = self.client.post('/send_command', payload_enable, content_type='application/json')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json(), {'Enabled': 'device1'})
            self.assertEqual(mock_parse_command.call_count, 2)

        # Remove test configs from disk
        clean_up_test_nodes()


# Test HTTP endpoints that make API requests to nodes and return the response
class HTTPEndpointTests(TestCase):
    def setUp(self):
        # Create 3 test nodes
        create_test_nodes()

    def tearDown(self):
        # Remove test configs from disk
        clean_up_test_nodes()

    def test_get_climate_data(self):
        # Mock request to return climate data
        with patch('api.views.request', return_value={'humid': 48.05045, 'temp': 70.25787}):
            response = self.client.get('/get_climate_data/Test1')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json(), {'humid': 48.05045, 'temp': 70.25787})

    def test_get_climate_data_offline(self):
        with patch('api.views.request', side_effect=OSError("Error: Unable to connect.")):
            response = self.client.get('/get_climate_data/Test1')
            self.assertEqual(response.status_code, 502)
            self.assertEqual(response.json(), "Error: Unable to connect.")

    def test_get_status(self):
        # Mock request to return status object
        with patch('api.views.request', return_value=config1_status_object):
            response = self.client.get('/get_status/Test1')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json(), config1_status_object)

    def test_get_status_offline(self):
        # Mock request to simulate offline target node
        with patch('api.views.request', side_effect=OSError("Error: Unable to connect.")):
            response = self.client.get('/get_status/Test1')
            self.assertEqual(response.status_code, 502)
            self.assertEqual(response.json(), "Error: Unable to connect.")


# Test model that stores and plays recorded macros
class MacroModelTests(TestCase):
    def setUp(self):
        # Create 3 test nodes
        create_test_nodes()

    def tearDown(self):
        # Remove test configs from disk
        clean_up_test_nodes()

    # Test instantiation, name standardization, __str__ method
    def test_instantiation(self):
        # Confirm no Macros
        self.assertEqual(len(Macro.objects.all()), 0)

        # Create with capitalized name, should convert to lowercase
        macro = Macro.objects.create(name='New Macro')
        macro.refresh_from_db()
        self.assertEqual(macro.name, 'new macro')
        self.assertEqual(macro.__str__(), 'New Macro')

        # Create with underscore and hyphen, should replace with spaces
        macro = Macro.objects.create(name='new-macro-name')
        macro.refresh_from_db()
        self.assertEqual(macro.name, 'new macro name')
        self.assertEqual(macro.__str__(), 'New Macro Name')

        # Create with numbers, should cast to string
        macro = Macro.objects.create(name=1337)
        macro.refresh_from_db()
        self.assertEqual(macro.name, '1337')
        self.assertEqual(macro.__str__(), '1337')

        # Confirm 3 macros created
        self.assertEqual(len(Macro.objects.all()), 3)

    # Should refuse to create the same name twice
    def test_no_duplicate_names(self):
        with self.assertRaises(IntegrityError):
            Macro.objects.create(name='New Macro')
            Macro.objects.create(name='New Macro')

    # Should refuse to create an empty name
    def test_no_empty_names(self):
        with self.assertRaises(IntegrityError):
            Macro.objects.create(name='')

    def test_add_and_delete_action(self):
        # Create test macro
        macro = Macro.objects.create(name='New Macro')

        # Add action, confirm 1 action exists, confirm value correct
        macro.add_action({"command": "turn_off", "instance": "device1", "target": "192.168.1.123", "friendly_name": "Countertop LEDs"})
        actions = json.loads(macro.actions)
        self.assertEqual(len(actions), 1)
        self.assertEqual(actions[0], {'ip': '192.168.1.123', 'args': ['turn_off', 'device1'], 'node_name': 'Test1', 'target_name': 'Countertop LEDs', 'action_name': 'Turn Off'})

        # Delete the just-created action, confirm removed
        macro.del_action(0)
        actions = json.loads(macro.actions)
        self.assertEqual(len(actions), 0)

        # Remove test configs from disk
        clean_up_test_nodes()

    def test_add_action_invalid(self):
        # Create test macro
        macro = Macro.objects.create(name='New Macro')

        # Attempt to add incomplete action (args only, no containing dict)
        with self.assertRaises(SyntaxError):
            macro.add_action(['turn_on', 'device1'])

        # Attempt to add action targeting instance that doesn't exist
        with self.assertRaises(KeyError):
            macro.add_action({"command": "turn_off", "instance": "device5", "target": "192.168.1.123", "friendly_name": "Countertop LEDs"})

        # Attempt to add ir action to node with no ir blaster
        with self.assertRaises(KeyError):
            macro.add_action({"command": "ir", "ir_target": "tv", "key": "power", "target": "192.168.1.123"})

    def test_delete_action_invalid(self):
        # Create test macro with 1 action
        macro = Macro.objects.create(name='New Macro')
        macro.add_action({"command": "set_rule", "instance": "device1", "rule": "248", "target": "192.168.1.123", "friendly_name": "Countertop LEDs"})

        # Attempt to delete a non-integer index
        with self.assertRaises(SyntaxError):
            macro.del_action("enable")

        # Attempt to delete out-of-range index
        with self.assertRaises(ValueError):
            macro.del_action(5)

    # Should reformat certain commands for readability in edit macro modal
    def test_set_frontend_values(self):
        # Create test macro
        macro = Macro.objects.create(name='New Macro')

        # Add action containing set_rule, should change to Set Rule and append value
        macro.add_action({"command": "set_rule", "instance": "device1", "rule": "248", "target": "192.168.1.123", "friendly_name": "Countertop LEDs"})
        self.assertEqual(json.loads(macro.actions)[0]['action_name'], 'Set Rule 248')

        # Add action containing ir command, should convert to "{target} {key}" format in frontend
        macro.add_action({"command": "ir", "ir_target": "ac", "key": "start", "target": "192.168.1.124"})
        self.assertEqual(json.loads(macro.actions)[1]['action_name'], 'Ac Start')

    # Confirm that new rules overwrite existing rules they would conflict with
    def test_no_conflicting_rules(self):
        # Create test macro
        macro = Macro.objects.create(name='New Macro')

        # Add 2 set_rule actions targeting the same instance with different values
        macro.add_action({"command": "set_rule", "instance": "device1", "rule": "248", "target": "192.168.1.123", "friendly_name": "Countertop LEDs"})
        macro.add_action({"command": "set_rule", "instance": "device1", "rule": "456", "target": "192.168.1.123", "friendly_name": "Countertop LEDs"})

        # Should only contain 1 action, should have most-recent value (456)
        self.assertEqual(len(json.loads(macro.actions)), 1)
        self.assertEqual(json.loads(macro.actions)[0]['action_name'], 'Set Rule 456')

        # Add both enable and disable targeting the same instance
        macro.add_action({"command": "enable", "instance": "device1", "target": "192.168.1.123", "friendly_name": "Countertop LEDs"})
        macro.add_action({"command": "disable", "instance": "device1", "target": "192.168.1.123", "friendly_name": "Countertop LEDs"})

        # Should only contain 1 additional rule, should have most-recent value (disable)
        self.assertEqual(len(json.loads(macro.actions)), 2)
        self.assertEqual(json.loads(macro.actions)[1]['action_name'], 'Disable')

        # Add both turn_on and turn_off targeting the same instance
        macro.add_action({"command": "turn_on", "instance": "device1", "target": "192.168.1.123", "friendly_name": "Countertop LEDs"})
        macro.add_action({"command": "turn_off", "instance": "device1", "target": "192.168.1.123", "friendly_name": "Countertop LEDs"})

        # Should only contain 1 additional rule, should have most-recent value (turn_off)
        self.assertEqual(len(json.loads(macro.actions)), 3)
        self.assertEqual(json.loads(macro.actions)[2]['action_name'], 'Turn Off')


# Test endpoints used to record and edit macros
class MacroTests(TestCase):
    def setUp(self):
        # Create 3 test nodes
        create_test_nodes()

    def tearDown(self):
        # Remove test configs from disk
        clean_up_test_nodes()

    def test_macro_name_available(self):
        # Should be available
        response = self.client.get('/macro_name_available/New')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), 'Name New available.')

        # Create in database, should no longer be available
        Macro.objects.create(name='New')
        response = self.client.get('/macro_name_available/New')
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json(), 'Name New already in use.')

    def test_add_macro_action(self):
        # Confirm no macros
        self.assertEqual(len(Macro.objects.all()), 0)

        # Payload sent by frontend when user turns on node1 device1 in record mode
        payload = {'name': 'First Macro', 'action': {'command': 'turn_on', 'instance': 'device1', 'target': '192.168.1.123', 'friendly_name': 'Cabinet Lights'}}

        # Send request, verify response, verify macro created
        response = self.client.post('/add_macro_action', payload, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), 'Done')
        self.assertEqual(len(Macro.objects.all()), 1)

    def test_delete_macro_action(self):
        # Create macro, verify exists
        payload = {'name': 'First Macro', 'action': {'command': 'turn_on', 'instance': 'device1', 'target': '192.168.1.123', 'friendly_name': 'Cabinet Lights'}}
        response = self.client.post('/add_macro_action', payload, content_type='application/json')
        self.assertEqual(len(Macro.objects.all()), 1)

        # Call view to delete just-created action
        response = self.client.get('/delete_macro_action/First Macro/0')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), 'Done')

        # Should still exist
        # TODO the frontend deletes it when last action removed, should this be moved to backend?
        # Frontend will still need to check to reload, won't remove much code
        self.assertEqual(len(Macro.objects.all()), 1)

    def test_delete_macro(self):
        # Create macro, verify exists in database
        Macro.objects.create(name='test')
        self.assertEqual(len(Macro.objects.all()), 1)

        # Call view to delete macro
        response = self.client.get('/delete_macro/test')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), 'Done')
        self.assertEqual(len(Macro.objects.all()), 0)

    def test_run_macro(self):
        # Create macro with 2 actions, verify exists
        action1 = {'name': 'First Macro', 'action': {'command': 'turn_on', 'instance': 'device1', 'target': '192.168.1.123', 'friendly_name': 'Cabinet Lights'}}
        action2 = {'name': 'First Macro', 'action': {'command': 'enable', 'instance': 'device1', 'target': '192.168.1.123', 'friendly_name': 'Cabinet Lights'}}
        self.client.post('/add_macro_action', action1, content_type='application/json')
        self.client.post('/add_macro_action', action2, content_type='application/json')
        self.assertEqual(len(Macro.objects.all()), 1)

        # Mock parse_command to do nothing
        with patch('api.views.parse_command', return_value=True) as mock_parse_command:
            # Call view to run macro, confirm response, confirm parse_command called twice
            response = self.client.get('/run_macro/First Macro')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json(), 'Done')
            self.assertEqual(mock_parse_command.call_count, 2)


class InvalidMacroTests(TestCase):
    def setUp(self):
        # Create 3 test nodes
        create_test_nodes()

    def tearDown(self):
        # Remove test configs from disk
        clean_up_test_nodes()

    def test_add_macro_action_get_request(self):
        # Requires POST request
        response = self.client.get('/add_macro_action')
        self.assertEqual(response.status_code, 405)
        self.assertEqual(response.json(), {'Error': 'Must post data'})

    def test_add_invalid_macro_action(self):
        # Confirm no macros
        self.assertEqual(len(Macro.objects.all()), 0)

        # Payload containing non-existing device5
        payload = {'name': 'First Macro', 'action': {'command': 'turn_on', 'instance': 'device5', 'target': '192.168.1.123', 'friendly_name': 'Not Real'}}

        # Send request, verify response, verify macro not created
        response = self.client.post('/add_macro_action', payload, content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), 'Invalid action')
        self.assertEqual(len(Macro.objects.all()), 0)

    def test_delete_invalid_macro_action(self):
        # Create macro, verify exists
        payload = {'name': 'First Macro', 'action': {'command': 'turn_on', 'instance': 'device1', 'target': '192.168.1.123', 'friendly_name': 'Cabinet Lights'}}
        response = self.client.post('/add_macro_action', payload, content_type='application/json')
        self.assertEqual(len(Macro.objects.all()), 1)

        # Attempt to delete non-existing macro action, verify response
        response = self.client.get('/delete_macro_action/First Macro/5')
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), 'ERROR: Macro action does not exist.')
        self.assertEqual(len(Macro.objects.all()), 1)

    def test_invalid_macro_does_not_exist(self):
        # Confirm no macros
        self.assertEqual(len(Macro.objects.all()), 0)

        # Call all endpoints, confirm correct error
        response = self.client.get('/run_macro/not-real')
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), 'Error: Macro not-real does not exist.')

        response = self.client.get('/delete_macro/not-real')
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), 'Error: Macro not-real does not exist.')

        response = self.client.get('/delete_macro_action/not-real/1')
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), 'Error: Macro not-real does not exist.')


# Test actions in overview top-right dropdown menu
class TestGlobalCommands(TestCase):
    def setUp(self):
        create_test_nodes()

    def tearDown(self):
        # Remove test configs from disk
        clean_up_test_nodes()

    def test_reset_all(self):
        # Mock request to return expected response for each node
        with patch('api.views.request', return_value={'device1': 'Reverted to scheduled rule', 'current_rule': 'disabled'}):
            # Create 3 test nodes
            response = self.client.get('/reset_all')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json(), "Done")

    def test_reset_all_offline(self):
        # Mock request to simulate offline nodes
        with patch('api.views.asyncio.open_connection', side_effect=OSError):
            # Create 3 test nodes
            response = self.client.get('/reset_all')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json(), "Done")

    def test_reboot_all(self):
        # Mock request to return expected response for each node
        with patch('api.views.request', return_value='Rebooting'):
            # Create 3 test nodes
            response = self.client.get('/reboot_all')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json(), "Done")

    def test_reboot_all_offline(self):
        # Mock request to simulate offline nodes
        with patch('api.views.asyncio.open_connection', side_effect=OSError):
            # Create 3 test nodes
            response = self.client.get('/reboot_all')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json(), "Done")


# Test successful calls to all API endpoints with mocked return values
class TestEndpoints(TestCase):

    def test_status(self):
        # Mock request to return status object
        with patch('api.views.request', return_value=config1_status_object):
            # Request status, should receive expected object
            response = parse_command('192.168.1.123', ['status'])
            self.assertEqual(response, config1_status_object)

    def test_reboot(self):
        # Mock request to return expected response
        with patch('api.views.request', return_value='Rebooting'):
            # Send request, verify response
            response = parse_command('192.168.1.123', ['reboot'])
            self.assertEqual(response, 'Rebooting')

    def test_disable(self):
        # Mock request to return expected response
        with patch('api.views.request', return_value={'Disabled': 'device1'}):
            # Send request, verify response
            response = parse_command('192.168.1.123', ['disable', 'device1'])
            self.assertEqual(response, {'Disabled': 'device1'})

    def test_disable_in(self):
        # Mock request to return expected response
        with patch('api.views.request', return_value={'Disabled': 'device1', 'Disable_in_seconds': 300.0}):
            # Send request, verify response
            response = parse_command('192.168.1.123', ['disable_in', 'device1', '5'])
            self.assertEqual(response, {'Disabled': 'device1', 'Disable_in_seconds': 300.0})

    def test_enable(self):
        # Mock request to return expected response
        with patch('api.views.request', return_value={'Enabled': 'device1'}):
            # Send request, verify response
            response = parse_command('192.168.1.123', ['enable', 'device1'])
            self.assertEqual(response, {'Enabled': 'device1'})

    def test_enable_in(self):
        # Mock request to return expected response
        with patch('api.views.request', return_value={'Enabled': 'device1', 'Enable_in_seconds': 300.0}):
            # Send request, verify response
            response = parse_command('192.168.1.123', ['enable_in', 'device1', '5'])
            self.assertEqual(response, {'Enabled': 'device1', 'Enable_in_seconds': 300.0})

    def test_set_rule(self):
        # Mock request to return expected response
        with patch('api.views.request', return_value={"device1": "50"}):
            # Send request, verify response
            response = parse_command('192.168.1.123', ['set_rule', 'device1', '50'])
            self.assertEqual(response, {"device1": "50"})

    def test_reset_rule(self):
        # Mock request to return expected response
        with patch('api.views.request', return_value={'device1': 'Reverted to scheduled rule', 'current_rule': 'disabled'}):
            # Send request, verify response
            response = parse_command('192.168.1.123', ['reset_rule', 'device1'])
            self.assertEqual(response, {'device1': 'Reverted to scheduled rule', 'current_rule': 'disabled'})

    def test_reset_all_rules(self):
        # Mock request to return expected response
        with patch('api.views.request', return_value={'New rules': {'device1': 'disabled', 'sensor1': 2.0, 'device2': 'enabled'}}):
            # Send request, verify response
            response = parse_command('192.168.1.123', ['reset_all_rules'])
            self.assertEqual(response, {'New rules': {'device1': 'disabled', 'sensor1': 2.0, 'device2': 'enabled'}})

    def test_get_schedule_rules(self):
        # Mock request to return expected response
        with patch('api.views.request', return_value={'05:00': 'enabled', '22:00': 'disabled'}):
            # Send request, verify response
            response = parse_command('192.168.1.123', ['get_schedule_rules', 'device2'])
            self.assertEqual(response, {'05:00': 'enabled', '22:00': 'disabled'})

    def test_add_rule(self):
        # Mock request to return expected response
        with patch('api.views.request', return_value={'time': '10:00', 'Rule added': 'disabled'}):
            # Send request, verify response
            response = parse_command('192.168.1.123', ['add_rule', 'device2', '10:00', 'disabled'])
            self.assertEqual(response, {'time': '10:00', 'Rule added': 'disabled'})

    def test_remove_rule(self):
        # Mock request to return expected response
        with patch('api.views.request', return_value={'Deleted': '10:00'}):
            # Send request, verify response
            response = parse_command('192.168.1.123', ['remove_rule', 'device2', '10:00'])
            self.assertEqual(response, {'Deleted': '10:00'})

    def test_save_rules(self):
        # Mock request to return expected response
        with patch('api.views.request', return_value={'Success': 'Rules written to disk'}):
            # Send request, verify response
            response = parse_command('192.168.1.123', ['save_rules'])
            self.assertEqual(response, {'Success': 'Rules written to disk'})

    def test_get_attributes(self):
        attributes = {'min_bright': 0, 'nickname': 'Cabinet Lights', 'bright': 0, 'scheduled_rule': 'disabled', 'current_rule': 'disabled', 'default_rule': 1023, 'enabled': False, 'rule_queue': ['1023', 'fade/256/7140', 'fade/32/7200', 'Disabled', '1023', 'fade/256/7140'], 'state': False, 'name': 'device1', 'triggered_by': ['sensor1'], 'max_bright': 1023, 'device_type': 'pwm', 'group': 'group1', 'fading': False}

        # Mock request to return expected response
        with patch('api.views.request', return_value=attributes):
            # Send request, verify response
            response = parse_command('192.168.1.123', ['get_attributes', 'device2'])
            self.assertEqual(response, attributes)

    def test_ir_key(self):
        # Mock request to return expected response
        with patch('api.views.request', return_value={'tv': 'power'}):
            # Send request, verify response
            response = parse_command('192.168.1.123', ['ir', 'tv', 'power'])
            self.assertEqual(response, {'tv': 'power'})

    def test_ir_backlight(self):
        # Mock request to return expected response
        with patch('api.views.request', return_value={'backlight': 'on'}):
            # Send request, verify response
            response = parse_command('192.168.1.123', ['ir', 'backlight', 'on'])
            self.assertEqual(response, {'backlight': 'on'})

    def test_get_temp(self):
        # Mock request to return expected response
        with patch('api.views.request', return_value={'Temp': 69.9683}):
            # Send request, verify response
            response = parse_command('192.168.1.123', ['get_temp'])
            self.assertEqual(response, {'Temp': 69.9683})

    def test_get_humid(self):
        # Mock request to return expected response
        with patch('api.views.request', return_value={'Humidity': 47.09677}):
            # Send request, verify response
            response = parse_command('192.168.1.123', ['get_humid'])
            self.assertEqual(response, {'Humidity': 47.09677})

    def test_get_climate(self):
        # Mock request to return expected response
        with patch('api.views.request', return_value={'humid': 47.12729, 'temp': 69.94899}):
            # Send request, verify response
            response = parse_command('192.168.1.123', ['get_climate'])
            self.assertEqual(response, {'humid': 47.12729, 'temp': 69.94899})

    def test_clear_log(self):
        # Mock request to return expected response
        with patch('api.views.request', return_value={'clear_log': 'success'}):
            # Send request, verify response
            response = parse_command('192.168.1.123', ['clear_log'])
            self.assertEqual(response, {'clear_log': 'success'})

    def test_condition_met(self):
        # Mock request to return expected response
        with patch('api.views.request', return_value={'Condition': False}):
            # Send request, verify response
            response = parse_command('192.168.1.123', ['condition_met', 'sensor1'])
            self.assertEqual(response, {'Condition': False})

    def test_trigger_sensor(self):
        # Mock request to return expected response
        with patch('api.views.request', return_value={'Triggered': 'sensor1'}):
            # Send request, verify response
            response = parse_command('192.168.1.123', ['trigger_sensor', 'sensor1'])
            self.assertEqual(response, {'Triggered': 'sensor1'})

    def test_turn_on(self):
        # Mock request to return expected response
        with patch('api.views.request', return_value={'On': 'device2'}):
            # Send request, verify response
            response = parse_command('192.168.1.123', ['turn_on', 'device2'])
            self.assertEqual(response, {'On': 'device2'})

    def test_turn_off(self):
        # Mock request to return expected response
        with patch('api.views.request', return_value={'Off': 'device2'}):
            # Send request, verify response
            response = parse_command('192.168.1.123', ['turn_off', 'device2'])
            self.assertEqual(response, {'Off': 'device2'})


# Test unsuccessful calls with invalid arguments to verify errors
class TestEndpointErrors(TestCase):

    def test_parse_command_missing_argument(self):
        # Call parse_command with no argument
        response = parse_command('192.168.1.123', [])
        self.assertEqual(response, "Error: No command received")

    def test_parse_command_invalid_argument(self):
        # Call parse_command with an argument that doesn't exist
        response = parse_command('192.168.1.123', ['self_destruct'])
        self.assertEqual(response, "Error: Command not found")

    def test_missing_required_argument(self):
        # Test endpoints with same missing arg error in loop
        for endpoint in ['disable', 'enable', 'disable_in', 'enable_in', 'set_rule', 'reset_rule', 'get_schedule_rules', 'add_rule', 'remove_rule', 'get_attributes', 'ir']:
            response = parse_command('192.168.1.123', [endpoint])
            self.assertEqual(response, {"ERROR": "Please fill out all fields"})

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
        self.assertEqual(response, {"ERROR": "Must specify time (HH:MM) followed by rule"})

    def test_add_rule_no_rule_arg(self):
        # Send request, verify response
        response = parse_command('192.168.1.123', ['add_rule', 'device1', '01:30'])
        self.assertEqual(response, {"ERROR": "Must specify new rule"})

    def test_remove_rule_invalid_arg(self):
        # Send request, verify response
        response = parse_command('192.168.1.123', ['remove_rule', 'not-a-device'])
        self.assertEqual(response, {"ERROR": "Only devices and sensors have schedule rules"})

    def test_remove_rule_no_time_arg(self):
        # Send request, verify response
        response = parse_command('192.168.1.123', ['remove_rule', 'device1'])
        self.assertEqual(response, {"ERROR": "Must specify time (HH:MM) of rule to remove"})

    def test_get_attributes_invalid_arg(self):
        # Send request, verify response
        response = parse_command('192.168.1.123', ['get_attributes', 'not-a-device'])
        self.assertEqual(response, {"ERROR": "Must specify device or sensor"})

    def test_ir_backlight_no_arg(self):
        # Send request, verify response
        response = parse_command('192.168.1.123', ['ir', 'backlight'])
        self.assertEqual(response, {"ERROR": "Must specify 'on' or 'off'"})

    def test_ir_backlight_invalid_arg(self):
        # Send request, verify response
        response = parse_command('192.168.1.123', ['ir', 'backlight', 'foo'])
        self.assertEqual(response, {"ERROR": "Must specify 'on' or 'off'"})

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
        self.assertEqual(response, {"ERROR": "Must speficy one of the following commands: power, vol_up, vol_down, mute, up, down, left, right, enter, settings, exit, source"})

        response = parse_command('192.168.1.123', ['ir', 'ac'])
        self.assertEqual(response, {"ERROR": "Must speficy one of the following commands: ON, OFF, UP, DOWN, FAN, TIMER, UNITS, MODE, STOP, START"})

    # Original bug: Timestamp regex allowed both H:MM and HH:MM, should only allow HH:MM
    def test_regression_single_digit_hour(self):
        # Mock request to return expected response (should not run)
        with patch('api.views.request', return_value={'time': '5:00', 'Rule added': 'disabled'}):
            # Send request, should receive error instead of mock response
            response = parse_command('192.168.1.123', ['add_rule', 'device2', '5:00', 'disabled'])
            self.assertEqual(response, {"ERROR": "Must specify time (HH:MM) followed by rule"})

        # Mock request to return expected response (should not run)
        with patch('api.views.request', return_value={'Deleted': '5:00'}):
            # Send request, verify response
            response = parse_command('192.168.1.123', ['remove_rule', 'device2', '5:00'])
            self.assertEqual(response, {"ERROR": "Must specify time (HH:MM) of rule to remove"})


# Test endpoint that loads modal containing existing macro actions
class EditModalTests(TestCase):
    def setUp(self):
        # Create 3 test nodes
        create_test_nodes()

        # Create macro with a single action
        # Payload sent by frontend to turn on node1 device1
        payload = {
            'name': 'Test1',
            'action': {
                'command': 'turn_on',
                'instance': 'device1',
                'target': '192.168.1.123',
                'friendly_name': 'Cabinet Lights'
            }
        }
        self.client.post('/add_macro_action', payload, content_type='application/json')

    def tearDown(self):
        # Remove test configs from disk
        clean_up_test_nodes()

    def test_edit_macro_button(self):
        # Send request, confirm status and template used
        response = self.client.get('/edit_macro/Test1')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'api/edit_modal.html')

        # Confirm correct context
        self.assertEqual(response.context['name'], 'Test1')
        self.assertEqual(response.context['actions'], [{'ip': '192.168.1.123', 'args': ['turn_on', 'device1'], 'node_name': 'Test1', 'target_name': 'Cabinet Lights', 'action_name': 'Turn On'}])

    def test_edit_non_existing_macro(self):
        # Request a macro that does not exist, confirm error
        response = self.client.get('/edit_macro/Test42')
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), 'Error: Macro Test42 does not exist.')


# Test endpoint that sets cookie to skip macro instructions modal
class SkipInstructionsTests(TestCase):
    def test_get_skip_instructions_cookie(self):
        response = self.client.get('/skip_instructions')
        self.assertEqual(response.status_code, 200)
        self.assertTrue('skip_instructions' in response.cookies)
        self.assertEqual(response.cookies['skip_instructions'].value, 'true')


# Test legacy api page
class LegacyApiTests(TestCase):
    def test_legacy_api_page(self):
        # Create 3 test nodes
        create_test_nodes()

        # Request page, confirm correct template used
        response = self.client.get('/legacy_api')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'api/legacy_api.html')

        # Confirm context contains correct number of nodes
        self.assertEqual(len(response.context['context']), 3)

        # Confirm one button for each node
        self.assertContains(response, '<button onclick="select_node(this)" type="button" class="select_node btn btn-primary m-1" id="Test1">Test1</button>')
        self.assertContains(response, '<button onclick="select_node(this)" type="button" class="select_node btn btn-primary m-1" id="Test2">Test2</button>')
        self.assertContains(response, '<button onclick="select_node(this)" type="button" class="select_node btn btn-primary m-1" id="Test3">Test3</button>')

        # Remove test configs from disk
        clean_up_test_nodes()


# Test api overview page
class OverviewPageTests(TestCase):
    def test_overview_page_no_nodes(self):
        # Request page, confirm correct template used
        response = self.client.get('/api')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'api/overview.html')

        # Confirm correct context (empty template)
        self.assertEqual(response.context['nodes'], {})
        self.assertEqual(response.context['macros'], {})

        # Confirm no floor or macro sections
        self.assertNotContains(response, '<div id="floor1" class="section mt-3 mb-4 p-3">')
        self.assertNotContains(response, '<h1 class="text-center mt-5">Macros</h1>')

        # Confirm link to create first node
        self.assertContains(response, '<h2>No Nodes Configured</h2>')
        self.assertContains(response, '<p>Click <a href="/new_config">here</a> to create</p>')

    def test_overview_page_with_nodes(self):
        # Create 3 test nodes
        create_test_nodes()

        # Request page, confirm correct template used
        response = self.client.get('/api')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'api/overview.html')

        # Confirm context contains correct number of nodes on each floor
        self.assertEqual(len(response.context['nodes'][1]), 2)
        self.assertEqual(len(response.context['nodes'][2]), 1)
        self.assertEqual(response.context['macros'], {})

        # Confirm floor and macro sections both present
        self.assertContains(response, '<div id="floor1" class="section mt-3 mb-4 p-3">')
        self.assertContains(response, '<h1 class="text-center mt-5">Macros</h1>')

        # Confirm no link to create node
        self.assertNotContains(response, '<h2>No Nodes Configured</h2>')
        self.assertNotContains(response, '<p>Click <a href="/new_config">here</a> to create</p>')

        # Remove test configs from disk
        clean_up_test_nodes()

    def test_overview_page_with_macro(self):
        # Create 3 test nodes
        create_test_nodes()

        # Expected macro context object
        test_macro_context = {'test macro': [{'ip': '192.168.1.123', 'args': ['trigger_sensor', 'sensor1'], 'node_name': 'Test1', 'target_name': 'Motion Sensor', 'action_name': 'Trigger Sensor'}, {'ip': '192.168.1.123', 'args': ['disable', 'device1'], 'node_name': 'Test1', 'target_name': 'Cabinet Lights', 'action_name': 'Disable'}, {'ip': '192.168.1.123', 'args': ['enable', 'device2'], 'node_name': 'Test1', 'target_name': 'Overhead Lights', 'action_name': 'Enable'}]}

        # Create macro with same actions as expected context
        Macro.objects.create(name='Test Macro', actions=json.dumps(test_macro_context['test macro']))

        # Request page, confirm correct template used, confirm context contains macro
        response = self.client.get('/api')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'api/overview.html')
        self.assertEqual(response.context['macros'], test_macro_context)

        # Confirm macro section present with correct-name macro
        self.assertContains(response, '<h1 class="text-center mt-5">Macros</h1>')
        self.assertContains(response, '<h3 class="mx-auto my-auto">Test Macro</h3>')

        # Remove test configs from disk
        clean_up_test_nodes()

    def test_overview_page_record_macro(self):
        # Create 3 test nodes
        create_test_nodes()

        # Request page with params to start recording macro named "New Macro Name"
        response = self.client.get('/api/recording/New Macro Name/start')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'api/overview.html')

        # Confirm context includes correct variables
        self.assertEqual(response.context['recording'], 'New Macro Name')
        self.assertEqual(response.context['start_recording'], True)

        # Confirm contains instructions modal
        self.assertContains(response, '<h3 class="mx-auto mb-0" id="error-modal-title">Macro Instructions</h3>')

        # Set cookie to skip instructions (checkbox in popup), request page again
        self.client.cookies['skip_instructions'] = 'true'
        response = self.client.get('/api/recording/New Macro Name/start')
        self.assertEqual(response.status_code, 200)

        # Should not contain instructions modal, context should include skip_instructions variable
        self.assertNotContains(response, '<h3 class="mx-auto mb-0" id="error-modal-title">Macro Instructions</h3>')
        self.assertEqual(response.context['skip_instructions'], True)

        # Remove test configs from disk
        clean_up_test_nodes()


# Test API Card interface
class ApiCardTests(TestCase):
    def setUp(self):
        # Create 3 test nodes
        create_test_nodes()

    def tearDown(self):
        # Remove test configs from disk
        clean_up_test_nodes()

    def test_api_frontend(self):
        # Mock request to return the expected status object
        with patch('api.views.request', return_value=config1_status_object):
            # Request page, confirm correct template used
            response = self.client.get('/api/Test1')
            self.assertEqual(response.status_code, 200)
            self.assertTemplateUsed(response, 'api/api_card.html')

            # Confirm all context keys
            self.assertEqual(response.context['context']['metadata'], config1_api_context['metadata'])
            self.assertEqual(response.context['context']['sensors'], config1_api_context['sensors'])
            self.assertEqual(response.context['context']['devices'], config1_api_context['devices'])

    # Repeat test above with a node containing ApiTarget and Thermostat
    def test_api_target_and_thermostat(self):
        # Mock request to return the expected status object
        with patch('api.views.request', return_value=config2_status_object):
            # Request page, confirm correct template used
            response = self.client.get('/api/Test2')
            self.assertEqual(response.status_code, 200)
            self.assertTemplateUsed(response, 'api/api_card.html')

            # Confirm all context keys
            self.assertEqual(response.context['context']['metadata'], config2_api_context['metadata'])
            self.assertEqual(response.context['context']['sensors'], config2_api_context['sensors'])
            self.assertEqual(response.context['context']['devices'], config2_api_context['devices'])
            self.assertEqual(response.context['context']['api_target_options'], config2_api_context['api_target_options'])

    def test_failed_connection(self):
        # Mock request to simulate offline target node
        with patch('api.views.request', side_effect=OSError("Error: Unable to connect.")):
            # Request page, confirm unable_to_connect template used
            response = self.client.get('/api/Test1')
            self.assertEqual(response.status_code, 200)
            self.assertTemplateUsed(response, 'api/unable_to_connect.html')

            # Confirm context
            self.assertEqual(response.context['context']['ip'], '192.168.1.123')
            self.assertEqual(response.context['context']['id'], 'Test1')

        # Mock parse_command to simulate timed out request
        with patch('api.views.parse_command', return_value='Error: Request timed out'):
            # Request page, confirm correct template used
            response = self.client.get('/api/Test1')
            self.assertEqual(response.status_code, 200)
            self.assertTemplateUsed(response, 'api/unable_to_connect.html')

    def test_recording_mode(self):
        # Mock request to return the expected status object
        with patch('api.views.request', return_value=config1_status_object):
            # Request page, confirm correct template used
            response = self.client.get('/api/Test1/macro-name')
            self.assertEqual(response.status_code, 200)
            self.assertTemplateUsed(response, 'api/api_card.html')

            # Confirm context contains macro name
            self.assertEqual(response.context['context']['metadata']['recording'], 'macro-name')


# Test modal used to edit schedule rules
class RuleModalTests(TestCase):
    def setUp(self):
        # Create 3 test nodes
        create_test_nodes()

    def tearDown(self):
        # Remove test configs from disk
        clean_up_test_nodes()

    # Get request is sent when adding a new rule
    def test_create_new_rule(self):
        response = self.client.get('/edit_rule')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'api/rule_modal.html')

    def test_edit_schedule_rule(self):
        # Send post request, confirm status and template used
        payload = {'timestamp': '14:00', 'rule': 'enabled', 'type': 'switch', 'target': 'sensor3', 'schedule_keywords': {'sunrise': '05:55', 'sunset': '20:20'}}
        response = self.client.post('/edit_rule', payload, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'api/rule_modal.html')

        # Confirm correct context
        self.assertEqual(response.context['timestamp'], '14:00')
        self.assertEqual(response.context['rule'], 'enabled')
        self.assertEqual(response.context['type'], 'switch')
        self.assertEqual(response.context['target'], 'sensor3')
        self.assertEqual(response.context['show_timestamp'], True)

    def test_edit_fade_rule(self):
        # Send post request, confirm status and template used
        payload = {'timestamp': '14:00', 'rule': 'fade/50/3600', 'type': 'dimmer', 'target': 'device1', 'schedule_keywords': {'sunrise': '05:55', 'sunset': '20:20'}}
        response = self.client.post('/edit_rule', payload, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'api/rule_modal.html')

        # Confirm correct context
        self.assertEqual(response.context['timestamp'], '14:00')
        self.assertEqual(response.context['fade'], True)
        self.assertEqual(response.context['rule'], '50')
        self.assertEqual(response.context['duration'], '3600')
        self.assertEqual(response.context['type'], 'dimmer')
        self.assertEqual(response.context['target'], 'device1')
        self.assertEqual(response.context['show_timestamp'], True)

    def test_edit_keyword_rule(self):
        # Send post request, confirm status and template used
        payload = {'timestamp': 'morning', 'rule': 'enabled', 'type': 'switch', 'target': 'sensor3', 'schedule_keywords': {'sunrise': '05:55', 'sunset': '20:20'}}
        response = self.client.post('/edit_rule', payload, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'api/rule_modal.html')

        # Confirm correct context
        self.assertEqual(response.context['timestamp'], 'morning')
        self.assertEqual(response.context['rule'], 'enabled')
        self.assertEqual(response.context['type'], 'switch')
        self.assertEqual(response.context['target'], 'sensor3')
        self.assertEqual(response.context['show_timestamp'], False)


# Test endpoints used to manage schedule keywords
class ScheduleKeywordTests(TestCase):
    def setUp(self):
        # Create 3 test nodes
        create_test_nodes()

    def tearDown(self):
        # Remove test configs from disk
        clean_up_test_nodes()

    def test_get_keywords(self):
        # Mock request to return expected response
        with patch('api.views.request', return_value={"sunrise": "05:55", "sunset": "20:20"}):
            # Send request, verify response
            response = parse_command('192.168.1.123', ['get_schedule_keywords'])
            self.assertEqual(response, {"sunrise": "05:55", "sunset": "20:20"})

    def test_add_keyword(self):
        # Mock request to return expected response
        with patch('api.views.request', return_value={"Keyword added": "test", "time": "05:00"}):
            # Send request, verify response
            response = parse_command('192.168.1.123', ['add_schedule_keyword', 'test', '05:00'])
            self.assertEqual(response, {"Keyword added": "test", "time": "05:00"})

    def test_remove_keyword(self):
        # Mock request to return expected response
        with patch('api.views.request', return_value={"Keyword removed": "test"}):
            # Send request, verify response
            response = parse_command('192.168.1.123', ['remove_schedule_keyword', 'test'])
            self.assertEqual(response, {"Keyword removed": "test"})

    def test_save_keywords(self):
        # Mock request to return expected response
        with patch('api.views.request', return_value={"Success": "Keywords written to disk"}):
            # Send request, verify response
            response = parse_command('192.168.1.123', ['save_schedule_keywords'])
            self.assertEqual(response, {"Success": "Keywords written to disk"})

    def test_sync_keywords(self):
        # Create 3 test keywords, confirm 5 total (sunrise + sunset already exist)
        ScheduleKeyword.objects.create(keyword='Test1', timestamp='12:34')
        ScheduleKeyword.objects.create(keyword='Test2', timestamp='23:45')
        ScheduleKeyword.objects.create(keyword='Test3', timestamp='04:56')
        self.assertEqual(len(ScheduleKeyword.objects.all()), 5)

        # Simulated request from node that already has all keywords
        payload = {
            'ip': '192.168.1.123',
            'existing_keywords': {
                    'sunrise': '05:49',
                    'sunset': '20:26',
                    'Test1': '12:34',
                    'Test2': '23:45',
                    'Test3': '04:56'
                }
        }

        # Mock parse_command to do nothing
        with patch('api.views.parse_command', return_value="Done") as mock_parse_command:
            # Send request, verify response
            response = self.client.post('/sync_schedule_keywords', payload, content_type='application/json')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json(), "Done")

            # Should not be called, no keywords to upload
            self.assertEqual(mock_parse_command.call_count, 0)

        # Delete 2 keywords, test again
        del payload['existing_keywords']['Test1']
        del payload['existing_keywords']['sunset']

        with patch('api.views.parse_command', return_value="Done") as mock_parse_command:
            response = self.client.post('/sync_schedule_keywords', payload, content_type='application/json')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json(), "Done")

            # Should be called 3 times - once for each keyword, once for save_schedule_keywords
            self.assertEqual(mock_parse_command.call_count, 3)

        # Delete all keywords, test again
        payload['existing_keywords'] = {}

        with patch('api.views.parse_command', return_value="Done") as mock_parse_command:
            response = self.client.post('/sync_schedule_keywords', payload, content_type='application/json')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json(), "Done")

            # Should be called 6 times - once for each keyword, once for save_schedule_keywords
            self.assertEqual(mock_parse_command.call_count, 6)

    def test_sync_keywords_errors(self):
        # Make invalid get request (requires post), confirm error
        response = self.client.get('/sync_schedule_keywords')
        self.assertEqual(response.status_code, 405)
        self.assertEqual(response.json(), {'Error': 'Must post data'})

    def test_add_errors(self):
        # Send request with no args, verify error
        response = parse_command('192.168.1.123', ['add_schedule_keyword'])
        self.assertEqual(response, {"ERROR": "Please fill out all fields"})

        # Send request with no timestamp, verify error
        response = parse_command('192.168.1.123', ['add_schedule_keyword', 'test'])
        self.assertEqual(response, {"ERROR": "Timestamp format must be HH:MM (no AM/PM)"})

    def test_remove_errors(self):
        # Send request with no args, verify error
        response = parse_command('192.168.1.123', ['remove_schedule_keyword'])
        self.assertEqual(response, {"ERROR": "Please fill out all fields"})

    # Original bug: Timestamp regex allowed both H:MM and HH:MM, should only allow HH:MM
    def test_regression_single_digit_hour(self):
        # Mock request to return expected response (should not run)
        with patch('api.views.request', return_value={"Keyword added": "test", "time": "5:00"}):
            # Send request, should receive error instead of mock response
            response = parse_command('192.168.1.123', ['add_schedule_keyword', 'test', '5:00'])
            self.assertEqual(response, {"ERROR": "Timestamp format must be HH:MM (no AM/PM)"})
