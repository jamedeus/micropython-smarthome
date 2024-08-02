from unittest.mock import patch
from django.test import TestCase
from .views import parse_command
from api_endpoints import ir_commands
from .unit_test_helpers import config1_status


# Test successful calls to all API endpoints with mocked return values
class TestEndpoints(TestCase):

    def test_status(self):
        # Mock request to return status object
        with patch('api_endpoints.request', return_value=config1_status):
            # Request status, should receive expected object
            response = parse_command('192.168.1.123', ['status'])
            self.assertEqual(response, config1_status)

    def test_reboot(self):
        # Mock request to return expected response
        with patch('api_endpoints.request', return_value='Rebooting'):
            # Send request, verify response
            response = parse_command('192.168.1.123', ['reboot'])
            self.assertEqual(response, 'Rebooting')

    def test_disable(self):
        # Mock request to return expected response
        expected_response = {'Disabled': 'device1'}
        with patch('api_endpoints.request', return_value=expected_response):
            # Send request, verify response
            response = parse_command('192.168.1.123', ['disable', 'device1'])
            self.assertEqual(response, expected_response)

    def test_disable_in(self):
        # Mock request to return expected response
        expected_response = {'Disabled': 'device1', 'Disable_in_seconds': 300.0}
        with patch('api_endpoints.request', return_value=expected_response):
            # Send request, verify response
            response = parse_command('192.168.1.123', ['disable_in', 'device1', '5'])
            self.assertEqual(response, expected_response)

    def test_enable(self):
        # Mock request to return expected response
        with patch('api_endpoints.request', return_value={'Enabled': 'device1'}):
            # Send request, verify response
            response = parse_command('192.168.1.123', ['enable', 'device1'])
            self.assertEqual(response, {'Enabled': 'device1'})

    def test_enable_in(self):
        # Mock request to return expected response
        expected_response = {'Enabled': 'device1', 'Enable_in_seconds': 300.0}
        with patch('api_endpoints.request', return_value=expected_response):
            # Send request, verify response
            response = parse_command('192.168.1.123', ['enable_in', 'device1', '5'])
            self.assertEqual(response, expected_response)

    def test_set_rule(self):
        # Mock request to return expected response
        expected_response = {"device1": "50"}
        with patch('api_endpoints.request', return_value=expected_response):
            # Send request, verify response
            response = parse_command('192.168.1.123', ['set_rule', 'device1', '50'])
            self.assertEqual(response, expected_response)

    def test_increment_rule(self):
        # Mock request to return expected response
        expected_response = {"device1": "100"}
        with patch('api_endpoints.request', return_value=expected_response):
            # Send request, verify response
            response = parse_command('192.168.1.123', ['increment_rule', 'device1', '50'])
            self.assertEqual(response, expected_response)

    def test_reset_rule(self):
        # Mock request to return expected response
        expected_response = {
            'device1': 'Reverted to scheduled rule',
            'current_rule': 'disabled'
        }
        with patch('api_endpoints.request', return_value=expected_response):
            # Send request, verify response
            response = parse_command('192.168.1.123', ['reset_rule', 'device1'])
            self.assertEqual(response, expected_response)

    def test_reset_all_rules(self):
        # Mock request to return expected response
        expected_response = {
            'New rules': {
                'device1': 'disabled',
                'sensor1': 2.0,
                'device2': 'enabled'
            }
        }
        with patch('api_endpoints.request', return_value=expected_response):
            # Send request, verify response
            response = parse_command('192.168.1.123', ['reset_all_rules'])
            self.assertEqual(response, expected_response)

    def test_get_schedule_rules(self):
        # Mock request to return expected response
        expected_response = {'05:00': 'enabled', '22:00': 'disabled'}
        with patch('api_endpoints.request', return_value=expected_response):
            # Send request, verify response
            response = parse_command('192.168.1.123', ['get_schedule_rules', 'device2'])
            self.assertEqual(response, expected_response)

    def test_add_rule(self):
        # Mock request to return expected response
        expected_response = {'time': '10:00', 'Rule added': 'disabled'}
        with patch('api_endpoints.request', return_value=expected_response):
            # Send request, verify response
            response = parse_command(
                '192.168.1.123',
                ['add_rule', 'device2', '10:00', 'disabled']
            )
            self.assertEqual(response, expected_response)

    def test_add_rule_keyword(self):
        # Mock request to return expected response
        expected_response = {'time': 'sunrise', 'Rule added': 'disabled'}
        with patch('api_endpoints.request', return_value=expected_response):
            # Send request, verify response
            response = parse_command(
                '192.168.1.123',
                ['add_rule', 'device2', 'sunrise', 'disabled']
            )
            self.assertEqual(response, expected_response)

    def test_remove_rule(self):
        # Mock request to return expected response
        expected_response = {'Deleted': '10:00'}
        with patch('api_endpoints.request', return_value=expected_response):
            # Send request, verify response
            response = parse_command('192.168.1.123', ['remove_rule', 'device2', '10:00'])
            self.assertEqual(response, expected_response)

    def test_remove_rule_keyword(self):
        # Mock request to return expected response
        expected_response = {'Deleted': 'sunrise'}
        with patch('api_endpoints.request', return_value=expected_response):
            # Send request, verify response
            response = parse_command('192.168.1.123', ['remove_rule', 'device2', 'sunrise'])
            self.assertEqual(response, expected_response)

    def test_save_rules(self):
        # Mock request to return expected response
        expected_response = {'Success': 'Rules written to disk'}
        with patch('api_endpoints.request', return_value=expected_response):
            # Send request, verify response
            response = parse_command('192.168.1.123', ['save_rules'])
            self.assertEqual(response, expected_response)

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
        expected_response = {'tv': 'power'}
        with patch('api_endpoints.request', return_value=expected_response):
            # Send request, verify response
            response = parse_command('192.168.1.123', ['ir', 'tv', 'power'])
            self.assertEqual(response, expected_response)

    def test_ir_get_existing_macros(self):
        # Mock request to return expected response
        with patch('api_endpoints.request', return_value={}):
            # Send request, verify response
            response = parse_command('192.168.1.123', ['ir_get_existing_macros'])
            self.assertEqual(response, {})

    def test_ir_create_macro(self):
        # Mock request to return expected response
        expected_response = {"Macro created": 'test1'}
        with patch('api_endpoints.request', return_value=expected_response):
            # Send request, verify response
            response = parse_command('192.168.1.123', ['ir_create_macro', 'test1'])
            self.assertEqual(response, expected_response)

    def test_ir_delete_macro(self):
        # Mock request to return expected response
        expected_response = {"Macro deleted": 'test1'}
        with patch('api_endpoints.request', return_value=expected_response):
            # Send request, verify response
            response = parse_command('192.168.1.123', ['ir_delete_macro', 'test1'])
            self.assertEqual(response, expected_response)

    def test_ir_save_macros(self):
        # Mock request to return expected response
        expected_response = {"Success": "Macros written to disk"}
        with patch('api_endpoints.request', return_value=expected_response):
            # Send request, verify response
            response = parse_command('192.168.1.123', ['ir_save_macros'])
            self.assertEqual(response, expected_response)

    def test_ir_add_macro_action(self):
        # Mock request to return expected response
        expected_response = {"Macro action added": ['test1', 'tv', 'power']}
        with patch('api_endpoints.request', return_value=expected_response):
            # Send request, verify response
            response = parse_command(
                '192.168.1.123',
                ['ir_add_macro_action', 'test1', 'tv', 'power']
            )
            self.assertEqual(response, expected_response)

    def test_ir_run_macro(self):
        # Mock request to return expected response
        expected_response = {"Ran macro": "test1"}
        with patch('api_endpoints.request', return_value=expected_response):
            # Send request, verify response
            response = parse_command(
                '192.168.1.123',
                ['ir_run_macro', 'test1', 'tv', 'power']
            )
            self.assertEqual(response, expected_response)

    def test_get_temp(self):
        # Mock request to return expected response
        expected_response = {'Temp': 69.9683}
        with patch('api_endpoints.request', return_value=expected_response):
            # Send request, verify response
            response = parse_command('192.168.1.123', ['get_temp'])
            self.assertEqual(response, expected_response)

    def test_get_humid(self):
        # Mock request to return expected response
        expected_response = {'Humidity': 47.09677}
        with patch('api_endpoints.request', return_value=expected_response):
            # Send request, verify response
            response = parse_command('192.168.1.123', ['get_humid'])
            self.assertEqual(response, expected_response)

    def test_get_climate(self):
        # Mock request to return expected response
        expected_response = {'humid': 47.12729, 'temp': 69.94899}
        with patch('api_endpoints.request', return_value=expected_response):
            # Send request, verify response
            response = parse_command('192.168.1.123', ['get_climate'])
            self.assertEqual(response, expected_response)

    def test_clear_log(self):
        # Mock request to return expected response
        expected_response = {'clear_log': 'success'}
        with patch('api_endpoints.request', return_value=expected_response):
            # Send request, verify response
            response = parse_command('192.168.1.123', ['clear_log'])
            self.assertEqual(response, expected_response)

    def test_condition_met(self):
        # Mock request to return expected response
        expected_response = {'Condition': False}
        with patch('api_endpoints.request', return_value=expected_response):
            # Send request, verify response
            response = parse_command('192.168.1.123', ['condition_met', 'sensor1'])
            self.assertEqual(response, expected_response)

    def test_trigger_sensor(self):
        # Mock request to return expected response
        expected_response = {'Triggered': 'sensor1'}
        with patch('api_endpoints.request', return_value=expected_response):
            # Send request, verify response
            response = parse_command('192.168.1.123', ['trigger_sensor', 'sensor1'])
            self.assertEqual(response, expected_response)

    def test_turn_on(self):
        # Mock request to return expected response
        expected_response = {'On': 'device2'}
        with patch('api_endpoints.request', return_value=expected_response):
            # Send request, verify response
            response = parse_command('192.168.1.123', ['turn_on', 'device2'])
            self.assertEqual(response, expected_response)

    def test_turn_off(self):
        # Mock request to return expected response
        expected_response = {'Off': 'device2'}
        with patch('api_endpoints.request', return_value=expected_response):
            # Send request, verify response
            response = parse_command('192.168.1.123', ['turn_off', 'device2'])
            self.assertEqual(response, expected_response)

    def test_set_gps_coords(self):
        # Mock request to return expected response
        expected_response = {"Success": "GPS coordinates set"}
        with patch('api_endpoints.request', return_value=expected_response):
            # Send request, verify response
            response = parse_command('192.168.1.123', ['set_gps_coords', '-90', '0.1'])
            self.assertEqual(response, expected_response)


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
        required_arg_endpoints = [
            "disable",
            "enable",
            "disable_in",
            "enable_in",
            "set_rule",
            "increment_rule",
            "reset_rule",
            "get_schedule_rules",
            "add_rule",
            "remove_rule",
            "get_attributes",
            "ir"
        ]

        # Test endpoints with same missing arg error in loop
        for endpoint in required_arg_endpoints:
            response = parse_command('192.168.1.123', [endpoint])
            self.assertEqual(response, 'Error: Missing required parameters')

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

    def test_increment_rule_invalid_arg(self):
        # Send request, verify response
        response = parse_command('192.168.1.123', ['increment_rule', 'not-a-device'])
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
        self.assertEqual(
            response,
            {"ERROR": "Must specify timestamp (HH:MM) or keyword followed by rule"}
        )

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
        self.assertEqual(
            response,
            {"ERROR": "Must specify timestamp (HH:MM) or keyword of rule to remove"}
        )

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
        self.assertEqual(
            response,
            {"ERROR": "Can only turn on/off devices, use enable/disable for sensors"}
        )

    def test_turn_off_invalid_arg(self):
        # Send request, verify response
        response = parse_command('192.168.1.123', ['turn_off', 'sensor1'])
        self.assertEqual(
            response,
            {"ERROR": "Can only turn on/off devices, use enable/disable for sensors"}
        )

    def test_ir_no_key(self):
        # Send request, verify response
        response = parse_command('192.168.1.123', ['ir', 'tv'])
        self.assertEqual(
            response,
            {"ERROR": f"Must specify one of the following commands: {ir_commands['tv']}"}
        )

        response = parse_command('192.168.1.123', ['ir', 'ac'])
        self.assertEqual(
            response,
            {"ERROR": f"Must specify one of the following commands: {ir_commands['ac']}"}
        )

    def test_ir_add_macro_action_missing_args(self):
        response = parse_command('192.168.1.123', ['ir_add_macro_action', 'test1'])
        self.assertEqual(response, 'Error: Missing required parameters')

    def test_set_gps_coords_missing_args(self):
        response = parse_command('192.168.1.123', ['set_gps_coords', '-90'])
        self.assertEqual(response, 'Error: Missing required parameters')

    # Original bug: Timestamp regex allowed both H:MM and HH:MM, should only allow HH:MM
    def test_regression_single_digit_hour(self):
        # Mock request to return expected response (should not run)
        expected_response = {'time': '5:00', 'Rule added': 'disabled'}
        with patch('api_endpoints.request', return_value=expected_response):
            # Send request, should receive error instead of mock response
            response = parse_command('192.168.1.123', ['add_rule', 'device2', '5:00', 'disabled'])
            self.assertEqual(
                response,
                {"ERROR": "Must specify timestamp (HH:MM) or keyword followed by rule"}
            )

        # Mock request to return expected response (should not run)
        with patch('api_endpoints.request', return_value={'Deleted': '5:00'}):
            # Send request, verify response
            response = parse_command('192.168.1.123', ['remove_rule', 'device2', '5:00'])
            self.assertEqual(
                response,
                {"ERROR": "Must specify timestamp (HH:MM) or keyword of rule to remove"}
            )

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
