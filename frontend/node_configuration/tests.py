import json
from copy import deepcopy
from django.test import TestCase
from .views import validate_full_config, get_api_target_menu_options
from .models import Config, Node, GpsCoordinates
from helper_functions import load_unit_test_config

# Large JSON objects, helper functions
from .unit_test_helpers import (
    JSONClient,
    request_payload,
    create_test_nodes,
    test_config_1_edit_context,
    test_config_2_edit_context,
    test_config_3_edit_context
)


# Test all endpoints that require POST requests
class ConfirmRequiresPostTests(TestCase):
    def test_get_request(self):
        # All endpoints requiring POST requests
        endpoints = [
            '/upload',
            '/upload/reupload',
            '/delete_config',
            '/delete_node',
            '/check_duplicate',
            '/generate_config_file',
            '/set_default_location',
            '/restore_config'
        ]

        # Confirm correct error and status code for each endpoint
        for endpoint in endpoints:
            response = self.client.get(endpoint)
            self.assertEqual(response.status_code, 405)
            self.assertEqual(response.json()['message'], 'Must post data')


# Test edit config view
class EditConfigTests(TestCase):
    def setUp(self):
        # Set default content_type for post requests (avoid long lines)
        self.client = JSONClient()

        # Create 3 test nodes and configs to edit
        create_test_nodes()

    def test_edit_config_1(self):
        # Request page, confirm correct template used
        response = self.client.get('/edit_config/Test1')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'node_configuration/edit-config.html')

        # Confirm correct context, keys in alphabetical order, correct api target menu options
        self.assertEqual(
            response.context['config'],
            test_config_1_edit_context['config']
        )
        self.assertEqual(
            list(response.context['config'].keys()),
            ['metadata', 'device1', 'device2', 'sensor1']
        )
        self.assertEqual(
            response.context['api_target_options'],
            test_config_1_edit_context['api_target_options']
        )

        # Confirm metadata context has devices and sensors keys
        self.assertEqual(
            list(response.context['metadata'].keys()),
            ['devices', 'sensors']
        )

        # Confirm edit mode
        self.assertEqual(response.context['edit_existing'], True)

    def test_edit_config_2(self):
        # Request page, confirm correct template used
        response = self.client.get('/edit_config/Test2')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'node_configuration/edit-config.html')

        # Confirm correct context + api target menu options
        self.assertEqual(
            response.context['config'],
            test_config_2_edit_context['config']
        )
        self.assertEqual(
            response.context['api_target_options'],
            test_config_2_edit_context['api_target_options']
        )

        # Confirm edit mode
        self.assertEqual(response.context['edit_existing'], True)

    def test_edit_config_3(self):
        # Request page, confirm correct template used
        response = self.client.get('/edit_config/Test3')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'node_configuration/edit-config.html')

        # Confirm correct context, keys in alphabetical order, correct api target menu options
        self.assertEqual(
            response.context['config'],
            test_config_3_edit_context['config']
        )
        self.assertEqual(
            list(response.context['config'].keys()),
            ['metadata', 'device1', 'device2', 'device3', 'sensor1', 'sensor2']
        )
        self.assertEqual(
            response.context['api_target_options'],
            test_config_3_edit_context['api_target_options']
        )

        # Confirm edit mode
        self.assertEqual(response.context['edit_existing'], True)

    # Original bug: Did not catch DoesNotExist error, leading to traceback
    # if target config was deleted by another client before clicking edit
    def test_regression_edit_non_existing_config(self):
        # Attempt to edit non-existing node, verify error
        response = self.client.get('/edit_config/Fake')
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()['message'], 'Fake node not found')


# Test config generation page
class ConfigGeneratorTests(TestCase):
    def test_new_config(self):
        # Request page, confirm correct template used
        response = self.client.get('/new_config')
        self.assertTemplateUsed(response, 'node_configuration/edit-config.html')

        # Expected config context with blank template
        expected_response = {
            'metadata': {
                'floor': '',
                'id': '',
                'location': '',
                'schedule_keywords': {
                    'sunrise': '06:00',
                    'sunset': '18:00'
                }
            }
        }

        # Confirm correct context (empty) + api target menu options + edit_existing set correctly
        self.assertEqual(response.context['config'], expected_response)
        self.assertEqual(response.context['api_target_options'], get_api_target_menu_options())
        self.assertEqual(response.context['edit_existing'], False)

        # Confirm metadata context has devices and sensors keys
        self.assertEqual(
            list(response.context['metadata'].keys()),
            ['devices', 'sensors']
        )


# Test duplicate detection
class DuplicateDetectionTests(TestCase):
    def setUp(self):
        # Set default content_type for post requests (avoid long lines)
        self.client = JSONClient()

    def test_check_duplicate(self):
        # Should accept new name
        response = self.client.post('/check_duplicate', {'name': 'Unit Test Config'})
        self.assertEqual(response.json()['message'], 'Name available')

        # Create config with same name
        self.client.post('/generate_config_file', request_payload)

        # Should now reject (identical name)
        response = self.client.post('/check_duplicate', {'name': 'Unit Test Config'})
        self.assertEqual(response.json()['message'], 'Config already exists with identical name')

        # Should reject regardless of capitalization
        response = self.client.post('/check_duplicate', {'name': 'Unit Test Config'})
        self.assertEqual(response.json()['message'], 'Config already exists with identical name')

        # Should accept different name
        response = self.client.post('/check_duplicate', {'name': 'Unit Test'})
        self.assertEqual(response.json()['message'], 'Name available')

    # Test second conditional in is_duplicate function (unreachable when used as
    # intended, prevents issues if advanced user creates Node from shell/admin)
    def test_duplicate_friendly_name_only(self):
        # Create Node with no matching Config (avoids matching first conditional)
        Node.objects.create(friendly_name="Unit Test Config", ip="123.45.67.89", floor="0")

        # Should reject, identical friendly name exists
        response = self.client.post('/check_duplicate', {'name': 'Unit Test Config'})
        self.assertEqual(response.json()['message'], 'Config already exists with identical name')


# Test config generator backend function
class GenerateConfigFileTests(TestCase):
    def setUp(self):
        # Set default content_type for post requests (avoid long lines)
        self.client = JSONClient()

        # Set default GPS coordinates
        GpsCoordinates.objects.create(
            display='Portland',
            lat='45.689122409097',
            lon='-122.63675124859863'
        )

    def test_generate_config_file(self):
        # Confirm starting condition
        self.assertEqual(len(Config.objects.all()), 0)

        # Post frontend config generator payload to view
        response = self.client.post('/generate_config_file', request_payload)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['message'], 'Config created')

        # Confirm model was created
        self.assertEqual(len(Config.objects.all()), 1)
        config = Config.objects.all()[0]

        # Confirm output file is same as known-value config
        compare = load_unit_test_config()
        self.assertEqual(config.config, compare)

    def test_edit_existing_config_file(self):
        # Create config, confirm 1 exists in database
        response = self.client.post('/generate_config_file', request_payload)
        self.assertEqual(len(Config.objects.all()), 1)

        # Copy request payload, change 1 default_rule
        modified_request_payload = deepcopy(request_payload)
        modified_request_payload['device6']['default_rule'] = 900

        # Send with edit arg (overwrite existing with same name instead of throwing duplicate error)
        response = self.client.post(
            '/generate_config_file/True',
            json.dumps(modified_request_payload)
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['message'], 'Config created')

        # Confirm same number of configs, no new config created
        self.assertEqual(len(Config.objects.all()), 1)
        config = Config.objects.all()[0]

        # Confirm new output is NOT identical to known-value config
        compare = load_unit_test_config()
        self.assertNotEqual(config.config, compare)

        # Change same default_rule, confirm was only change made
        compare['device6']['default_rule'] = 900
        self.assertEqual(config.config, compare)

    def test_duplicate_config_name(self):
        # Confirm starting condition
        self.assertEqual(len(Config.objects.all()), 0)

        # Post frontend config generator payload to view, confirm response + model created
        response = self.client.post('/generate_config_file', request_payload)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['message'], 'Config created')
        self.assertEqual(len(Config.objects.all()), 1)

        # Post again, should throw error (duplicate name), should not create model
        response = self.client.post('/generate_config_file', request_payload)
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()['message'], 'Config already exists with identical name')
        self.assertEqual(len(Config.objects.all()), 1)

    def test_invalid_config_file(self):
        # Confirm starting condition
        self.assertEqual(len(Config.objects.all()), 0)

        # Add invalid default rule to request payload
        invalid_request_payload = deepcopy(request_payload)
        invalid_request_payload['device6']['default_rule'] = 9001

        # Post invalid payload, confirm rejected with correct error, confirm config not created
        response = self.client.post('/generate_config_file', json.dumps(invalid_request_payload))
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['message'], 'Cabinet Lights: Invalid default rule 9001')
        self.assertEqual(len(Config.objects.all()), 0)

    # Original bug: Did not catch DoesNotExist error, leading to traceback
    # if target config was deleted by another client while editing
    def test_regression_edit_non_existing_config(self):
        # Attempt to edit non-existing config file, verify error, confirm not created
        response = self.client.post('/generate_config_file/True', request_payload)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()['message'], 'Config not found')
        self.assertEqual(len(Config.objects.all()), 0)

    # Original bug: Did not catch schedule rules with no timestamp (didn't make
    # node crash but should still reject, user may have forgot to add time)
    def test_regression_empty_schedule_rule_timestamp(self):
        # Confirm starting condition
        self.assertEqual(len(Config.objects.all()), 0)

        # Add schedule rule with empty timestamp
        invalid_request_payload = deepcopy(request_payload)
        invalid_request_payload['device2']['schedule'][''] = '100'

        # Post invalid payload, confirm rejected with correct error, confirm config not created
        response = self.client.post('/generate_config_file', json.dumps(invalid_request_payload))
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['message'], 'Lamp: Missing schedule rule timestamp')
        self.assertEqual(len(Config.objects.all()), 0)


# Test the validate_full_config function called when user submits config generator form
class ValidateConfigTests(TestCase):
    def setUp(self):
        self.valid_config = load_unit_test_config()

    def test_valid_config(self):
        result = validate_full_config(self.valid_config)
        self.assertTrue(result)

    def test_missing_keys(self):
        del self.valid_config['metadata']['id']
        result = validate_full_config(self.valid_config)
        self.assertEqual(result, 'Missing required key in metadata section')

        del self.valid_config['metadata']
        result = validate_full_config(self.valid_config)
        self.assertEqual(result, 'Missing required top-level metadata key')

    def test_invalid_floor(self):
        self.valid_config['metadata']['floor'] = 'top'
        result = validate_full_config(self.valid_config)
        self.assertEqual(result, 'Required metadata key floor has incorrect type')

    def test_duplicate_nicknames(self):
        self.valid_config['device4']['nickname'] = self.valid_config['device1']['nickname']
        result = validate_full_config(self.valid_config)
        self.assertEqual(result, 'Contains duplicate nicknames')

    def test_duplicate_pins(self):
        self.valid_config['sensor2']['pin'] = self.valid_config['sensor1']['pin']
        result = validate_full_config(self.valid_config)
        self.assertEqual(result, 'Contains duplicate pins')

    def test_invalid_device_pin(self):
        self.valid_config['device1']['pin'] = '14'
        result = validate_full_config(self.valid_config)
        self.assertEqual(
            result,
            f'Invalid device pin {self.valid_config["device1"]["pin"]} used'
        )

    def test_invalid_sensor_pin(self):
        self.valid_config['sensor1']['pin'] = '3'
        result = validate_full_config(self.valid_config)
        self.assertEqual(
            result,
            f'Invalid sensor pin {self.valid_config["sensor1"]["pin"]} used'
        )

    def test_noninteger_pin(self):
        self.valid_config['sensor1']['pin'] = 'three'
        result = validate_full_config(self.valid_config)
        self.assertEqual(result, 'Invalid pin (non-integer)')

    def test_invalid_device_type(self):
        self.valid_config['device1']['_type'] = 'nuclear'
        result = validate_full_config(self.valid_config)
        self.assertEqual(
            result,
            f'Invalid device type {self.valid_config["device1"]["_type"]} used'
        )

    def test_invalid_sensor_type(self):
        self.valid_config['sensor1']['_type'] = 'ozone-sensor'
        result = validate_full_config(self.valid_config)
        self.assertEqual(
            result,
            f'Invalid sensor type {self.valid_config["sensor1"]["_type"]} used'
        )

    def test_invalid_ip(self):
        self.valid_config['device1']['ip'] = '192.168.1.500'
        result = validate_full_config(self.valid_config)
        self.assertEqual(result, f'Invalid IP {self.valid_config["device1"]["ip"]}')

    def test_thermostat_tolerance_out_of_range(self):
        self.valid_config['sensor5']['tolerance'] = 12.5
        result = validate_full_config(self.valid_config)
        self.assertEqual(result, 'Thermostat tolerance out of range (0.1 - 10.0)')

    def test_invalid_thermostat_tolerance(self):
        self.valid_config['sensor5']['tolerance'] = 'low'
        result = validate_full_config(self.valid_config)
        self.assertEqual(result, 'Thermostat tolerance must be int or float')

    def test_pwm_min_greater_than_max(self):
        self.valid_config['device6']['min_rule'] = 1023
        self.valid_config['device6']['max_rule'] = 500
        self.valid_config['device6']['default_rule'] = 700
        result = validate_full_config(self.valid_config)
        self.assertEqual(result, 'min_rule cannot be greater than max_rule')

    def test_pwm_limits_negative(self):
        self.valid_config['device6']['min_rule'] = -50
        self.valid_config['device6']['max_rule'] = -5
        result = validate_full_config(self.valid_config)
        self.assertEqual(result, 'Rule limits cannot be less than 0')

    def test_pwm_limits_over_max(self):
        self.valid_config['device6']['min_rule'] = 1023
        self.valid_config['device6']['max_rule'] = 4096
        result = validate_full_config(self.valid_config)
        self.assertEqual(result, 'Rule limits cannot be greater than 1023')

    def test_pwm_invalid_default_rule(self):
        self.valid_config['device6']['min_rule'] = 500
        self.valid_config['device6']['max_rule'] = 1000
        self.valid_config['device6']['default_rule'] = 1100
        result = validate_full_config(self.valid_config)
        self.assertEqual(result, 'Cabinet Lights: Invalid default rule 1100')

    def test_pwm_invalid_schedule_rule(self):
        self.valid_config['device6']['min_rule'] = 500
        self.valid_config['device6']['max_rule'] = 1000
        self.valid_config['device6']['schedule']['01:00'] = 1023
        result = validate_full_config(self.valid_config)
        self.assertEqual(result, 'Cabinet Lights: Invalid schedule rule 1023')

    def test_pwm_noninteger_limit(self):
        self.valid_config['device6']['min_rule'] = 'off'
        result = validate_full_config(self.valid_config)
        self.assertEqual(
            result,
            'Invalid rule limits, both must be int between 0 and 1023'
        )
