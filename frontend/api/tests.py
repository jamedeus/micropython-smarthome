from django.test import TestCase
from django.conf import settings

from node_configuration.models import *
from node_configuration.unit_test_helpers import create_test_nodes, clean_up_test_nodes, create_config_and_node_from_json, test_config_1, test_config_2, test_config_3
from .models import Macro
from .views import parse_command
from .unit_test_helpers import *

import json
from unittest.mock import patch



# Test HTTP endpoints that make API requests to nodes and return the response
class HTTPEndpointTests(TestCase):
    def setUp(self):
        # Create 3 test nodes
        create_test_nodes()

    def test_get_climate_data(self):
        # Mock request to return climate data
        with patch('api.views.request', return_value = {'humid': 48.05045, 'temp': 70.25787}):
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
        with patch('api.views.request', return_value = config1_status_object):
            response = self.client.get('/get_status/Test1')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json(), config1_status_object)

    def test_get_status_offline(self):
        # Mock request to simulate offline target node
        with patch('api.views.request', side_effect=OSError("Error: Unable to connect.")):
            response = self.client.get('/get_status/Test1')
            self.assertEqual(response.status_code, 502)
            self.assertEqual(response.json(), "Error: Unable to connect.")



# Test actions in overview top-right dropdown menu
class TestGlobalCommands(TestCase):
    def setUp(self):
        create_test_nodes()

    def test_reset_all(self):
        # Mock request to return expected response for each node
        with patch('api.views.request', return_value = {'device1': 'Reverted to scheduled rule', 'current_rule': 'disabled'}):
            # Create 3 test nodes
            response = self.client.get('/reset_all')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json(), "Done")

    def test_reboot_all(self):
        # Mock request to return expected response for each node
        with patch('api.views.request', return_value = 'Rebooting'):
            # Create 3 test nodes
            response = self.client.get('/reboot_all')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json(), "Done")



# Test successful calls to all API endpoints with mocked return values
class TestEndpoints(TestCase):

    def test_status(self):
        # Mock request to return status object
        with patch('api.views.request', return_value = config1_status_object):
            # Request status, should receive expected object
            response = parse_command('192.168.1.123', ['status'])
            self.assertEqual(response, config1_status_object)

    def test_reboot(self):
        # Mock request to return expected response
        with patch('api.views.request', return_value = 'Rebooting'):
            # Send request, verify response
            response = parse_command('192.168.1.123', ['reboot'])
            self.assertEqual(response, 'Rebooting')

    def test_disable(self):
        # Mock request to return expected response
        with patch('api.views.request', return_value = {'Disabled': 'device1'}):
            # Send request, verify response
            response = parse_command('192.168.1.123', ['disable', 'device1'])
            self.assertEqual(response, {'Disabled': 'device1'})

    def test_disable_in(self):
        # Mock request to return expected response
        with patch('api.views.request', return_value = {'Disabled': 'device1', 'Disable_in_seconds': 300.0}):
            # Send request, verify response
            response = parse_command('192.168.1.123', ['disable_in', 'device1', '5'])
            self.assertEqual(response, {'Disabled': 'device1', 'Disable_in_seconds': 300.0})

    def test_enable(self):
        # Mock request to return expected response
        with patch('api.views.request', return_value = {'Enabled': 'device1'}):
            # Send request, verify response
            response = parse_command('192.168.1.123', ['enable', 'device1'])
            self.assertEqual(response, {'Enabled': 'device1'})

    def test_enable_in(self):
        # Mock request to return expected response
        with patch('api.views.request', return_value = {'Enabled': 'device1', 'Enable_in_seconds': 300.0}):
            # Send request, verify response
            response = parse_command('192.168.1.123', ['enable_in', 'device1', '5'])
            self.assertEqual(response, {'Enabled': 'device1', 'Enable_in_seconds': 300.0})

    def test_set_rule(self):
        # Mock request to return expected response
        with patch('api.views.request', return_value = {"device1": "50"}):
            # Send request, verify response
            response = parse_command('192.168.1.123', ['set_rule', 'device1', '50'])
            self.assertEqual(response, {"device1": "50"})

    def test_reset_rule(self):
        # Mock request to return expected response
        with patch('api.views.request', return_value = {'device1': 'Reverted to scheduled rule', 'current_rule': 'disabled'}):
            # Send request, verify response
            response = parse_command('192.168.1.123', ['reset_rule', 'device1'])
            self.assertEqual(response, {'device1': 'Reverted to scheduled rule', 'current_rule': 'disabled'})

    def test_reset_all_rules(self):
        # Mock request to return expected response
        with patch('api.views.request', return_value = {'New rules': {'device1': 'disabled', 'sensor1': 2.0, 'device2': 'enabled'}}):
            # Send request, verify response
            response = parse_command('192.168.1.123', ['reset_all_rules'])
            self.assertEqual(response, {'New rules': {'device1': 'disabled', 'sensor1': 2.0, 'device2': 'enabled'}})

    def test_get_schedule_rules(self):
        # Mock request to return expected response
        with patch('api.views.request', return_value = {'05:00': 'enabled', '22:00': 'disabled'}):
            # Send request, verify response
            response = parse_command('192.168.1.123', ['get_schedule_rules', 'device2'])
            self.assertEqual(response, {'05:00': 'enabled', '22:00': 'disabled'})

    def test_add_rule(self):
        # Mock request to return expected response
        with patch('api.views.request', return_value = {'time': '10:00', 'Rule added': 'disabled'}):
            # Send request, verify response
            response = parse_command('192.168.1.123', ['add_rule', 'device2', '10:00', 'disabled'])
            self.assertEqual(response, {'time': '10:00', 'Rule added': 'disabled'})

    def test_remove_rule(self):
        # Mock request to return expected response
        with patch('api.views.request', return_value = {'Deleted': '10:00'}):
            # Send request, verify response
            response = parse_command('192.168.1.123', ['remove_rule', 'device2', '10:00'])
            self.assertEqual(response, {'Deleted': '10:00'})

    def test_save_rules(self):
        # Mock request to return expected response
        with patch('api.views.request', return_value = {'Success': 'Rules written to disk'}):
            # Send request, verify response
            response = parse_command('192.168.1.123', ['save_rules'])
            self.assertEqual(response, {'Success': 'Rules written to disk'})

    def test_get_attributes(self):
        attributes = {'min_bright': 0, 'nickname': 'Cabinet Lights', 'bright': 0, 'scheduled_rule': 'disabled', 'current_rule': 'disabled', 'default_rule': 1023, 'enabled': False, 'rule_queue': ['1023', 'fade/256/7140', 'fade/32/7200', 'Disabled', '1023', 'fade/256/7140'], 'state': False, 'name': 'device1', 'triggered_by': ['sensor1'], 'max_bright': 1023, 'device_type': 'pwm', 'group': 'group1', 'fading': False}

        # Mock request to return expected response
        with patch('api.views.request', return_value = attributes):
            # Send request, verify response
            response = parse_command('192.168.1.123', ['get_attributes', 'device2'])
            self.assertEqual(response, attributes)

    def test_ir_key(self):
        # Mock request to return expected response
        with patch('api.views.request', return_value = {'tv': 'power'}):
            # Send request, verify response
            response = parse_command('192.168.1.123', ['ir', 'tv', 'power'])
            self.assertEqual(response, {'tv': 'power'})

    def test_ir_backlight(self):
        # Mock request to return expected response
        with patch('api.views.request', return_value = {'backlight': 'on'}):
            # Send request, verify response
            response = parse_command('192.168.1.123', ['ir', 'backlight', 'on'])
            self.assertEqual(response, {'backlight': 'on'})

    def test_get_temp(self):
        # Mock request to return expected response
        with patch('api.views.request', return_value = {'Temp': 69.9683}):
            # Send request, verify response
            response = parse_command('192.168.1.123', ['get_temp'])
            self.assertEqual(response, {'Temp': 69.9683})

    def test_get_humid(self):
        # Mock request to return expected response
        with patch('api.views.request', return_value = {'Humidity': 47.09677}):
            # Send request, verify response
            response = parse_command('192.168.1.123', ['get_humid'])
            self.assertEqual(response, {'Humidity': 47.09677})

    def test_get_climate(self):
        # Mock request to return expected response
        with patch('api.views.request', return_value = {'humid': 47.12729, 'temp': 69.94899}):
            # Send request, verify response
            response = parse_command('192.168.1.123', ['get_climate'])
            self.assertEqual(response, {'humid': 47.12729, 'temp': 69.94899})

    def test_clear_log(self):
        # Mock request to return expected response
        with patch('api.views.request', return_value = {'clear_log': 'success'}):
            # Send request, verify response
            response = parse_command('192.168.1.123', ['clear_log'])
            self.assertEqual(response, {'clear_log': 'success'})

    def test_condition_met(self):
        # Mock request to return expected response
        with patch('api.views.request', return_value = {'Condition': False}):
            # Send request, verify response
            response = parse_command('192.168.1.123', ['condition_met', 'sensor1'])
            self.assertEqual(response, {'Condition': False})

    def test_trigger_sensor(self):
        # Mock request to return expected response
        with patch('api.views.request', return_value = {'Triggered': 'sensor1'}):
            # Send request, verify response
            response = parse_command('192.168.1.123', ['trigger_sensor', 'sensor1'])
            self.assertEqual(response, {'Triggered': 'sensor1'})

    def test_turn_on(self):
        # Mock request to return expected response
        with patch('api.views.request', return_value = {'On': 'device2'}):
            # Send request, verify response
            response = parse_command('192.168.1.123', ['turn_on', 'device2'])
            self.assertEqual(response, {'On': 'device2'})

    def test_turn_off(self):
        # Mock request to return expected response
        with patch('api.views.request', return_value = {'Off': 'device2'}):
            # Send request, verify response
            response = parse_command('192.168.1.123', ['turn_off', 'device2'])
            self.assertEqual(response, {'Off': 'device2'})



# Test unsuccessful calls with invalid arguments to verify errors
class TestEndpointErrors(TestCase):

    def test_missing_required_argument(self):
        # Test endpoints with same missing arg error in loop
        for endpoint in ['disable', 'enable', 'disable_in', 'enable_in', 'set_rule', 'reset_rule', 'get_schedule_rules', 'add_rule', 'remove_rule', 'get_attributes', 'ir']:
            response = parse_command('192.168.1.123', [endpoint])
            self.assertEqual(response, {"ERROR" : "Please fill out all fields"})

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



# Test endpoint that loads modal containing existing macro actions
class EditModalTests(TestCase):
    def setUp(self):
        # Create 3 test nodes
        create_test_nodes()

        # Create macro with a single action
        # Payload sent by frontend to turn on node1 device1
        payload = {'name': 'Test1', 'action': {'command': 'turn_on', 'instance': 'device1', 'target': '192.168.1.123', 'friendly_name': 'Cabinet Lights'}}
        self.client.post('/add_macro_action', payload, content_type='application/json')

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



# Test API Card interface
class ApiCardTests(TestCase):
    def setUp(self):
        # Create 3 test nodes
        create_test_nodes()

    def test_api_frontend(self):
        # Mock request to return the expected status object
        with patch('api.views.request', return_value = config1_status_object):
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
        with patch('api.views.request', return_value = config2_status_object):
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
        with patch('api.views.request', return_value = config1_status_object):
            # Request page, confirm correct template used
            response = self.client.get('/api/Test1/macro-name')
            self.assertEqual(response.status_code, 200)
            self.assertTemplateUsed(response, 'api/api_card.html')

            # Confirm context contains macro name
            self.assertEqual(response.context['context']['metadata']['recording'], 'macro-name')
