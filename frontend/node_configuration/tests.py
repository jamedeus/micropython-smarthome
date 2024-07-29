import os
import json
from io import StringIO
from copy import deepcopy
from django.conf import settings
from django.core.management import call_command
from django.core.management.base import CommandError
from .views import validate_full_config, get_api_target_menu_options
from .models import Config, Node, WifiCredentials, GpsCoordinates

# Functions used to manage cli_config.json
from helper_functions import get_cli_config, load_unit_test_config

# Large JSON objects, helper functions
from .unit_test_helpers import (
    TestCaseBackupRestore,
    JSONClient,
    request_payload,
    create_test_nodes,
    clean_up_test_nodes,
    test_config_1,
    test_config_2,
    test_config_3,
    test_config_1_edit_context,
    test_config_2_edit_context,
    test_config_3_edit_context
)

# Ensure CLI_SYNC is True (writes test configs to disk when created)
settings.CLI_SYNC = True

# Create CONFIG_DIR if it does not exist
if not os.path.exists(settings.CONFIG_DIR):
    os.mkdir(settings.CONFIG_DIR, mode=0o775)
    with open(os.path.join(settings.CONFIG_DIR, 'readme'), 'w') as file:
        file.write('This directory was automatically created for frontend unit tests.\n')
        file.write('You can safely delete it, it will be recreated each time tests run.')

# Create cli_config.json if it does not exist
if not os.path.exists(os.path.join(settings.REPO_DIR, 'CLI', 'cli_config.json')):
    from helper_functions import write_cli_config
    write_cli_config(get_cli_config())


# Test all endpoints that require POST requests
class ConfirmRequiresPostTests(TestCaseBackupRestore):
    def test_get_request(self):
        # All endpoints requiring POST requests
        endpoints = [
            '/upload',
            '/upload/reupload',
            '/delete_config',
            '/delete_node',
            '/check_duplicate',
            '/generate_config_file',
            '/set_default_credentials',
            '/set_default_location',
            '/restore_config'
        ]

        # Confirm correct error and status code for each endpoint
        for endpoint in endpoints:
            response = self.client.get(endpoint)
            self.assertEqual(response.status_code, 405)
            self.assertEqual(response.json()['message'], 'Must post data')


# Test edit config view
class EditConfigTests(TestCaseBackupRestore):
    def setUp(self):
        # Set default content_type for post requests (avoid long lines)
        self.client = JSONClient()

        # Create 3 test nodes and configs to edit
        create_test_nodes()

    def tearDown(self):
        # Remove test configs from disk
        clean_up_test_nodes()

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
            ['metadata', 'wifi', 'device1', 'device2', 'sensor1']
        )
        self.assertEqual(
            response.context['api_target_options'],
            test_config_1_edit_context['api_target_options']
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
            ['metadata', 'wifi', 'device1', 'device2', 'device3', 'sensor1', 'sensor2']
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
class ConfigGeneratorTests(TestCaseBackupRestore):
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
                'schedule_keywords': {'sunrise': '06:00', 'sunset': '18:00'}},
            'wifi': {'password': '', 'ssid': ''}
        }

        # Confirm correct context (empty) + api target menu options + edit_existing set correctly
        self.assertEqual(response.context['config'], expected_response)
        self.assertEqual(response.context['api_target_options'], get_api_target_menu_options())
        self.assertEqual(response.context['edit_existing'], False)

    def test_with_default_wifi(self):
        # Set default wifi credentials
        WifiCredentials.objects.create(ssid='AzureDiamond', password='hunter2')

        # Expected config context with wifi credentials pre-filled
        expected_response = {
            'metadata': {
                'floor': '',
                'id': '',
                'location': '',
                'schedule_keywords': {'sunrise': '06:00', 'sunset': '18:00'}},
            'wifi': {'password': 'hunter2', 'ssid': 'AzureDiamond'}
        }

        # Request page, confirm correct template used
        response = self.client.get('/new_config')
        self.assertTemplateUsed(response, 'node_configuration/edit-config.html')

        # Confirm context contains credentials + edit_existing set correctly
        self.assertEqual(response.context['config'], expected_response)
        self.assertEqual(response.context['edit_existing'], False)


# Test duplicate detection
class DuplicateDetectionTests(TestCaseBackupRestore):
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
class GenerateConfigFileTests(TestCaseBackupRestore):
    def setUp(self):
        # Set default content_type for post requests (avoid long lines)
        self.client = JSONClient()

        # Set default GPS coordinates
        GpsCoordinates.objects.create(
            display='Portland',
            lat='45.689122409097',
            lon='-122.63675124859863'
        )

    def tearDown(self):
        try:
            os.remove(os.path.join(settings.CONFIG_DIR, 'unit-test-config.json'))
        except FileNotFoundError:
            pass

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
class ValidateConfigTests(TestCaseBackupRestore):
    def setUp(self):
        self.valid_config = load_unit_test_config()

    def test_valid_config(self):
        result = validate_full_config(self.valid_config)
        self.assertTrue(result)

    def test_missing_keys(self):
        del self.valid_config['wifi']['ssid']
        result = validate_full_config(self.valid_config)
        self.assertEqual(result, 'Missing required key in wifi section')

        del self.valid_config['metadata']['id']
        result = validate_full_config(self.valid_config)
        self.assertEqual(result, 'Missing required key in metadata section')

        del self.valid_config['metadata']
        result = validate_full_config(self.valid_config)
        self.assertEqual(result, 'Missing required top-level metadata key')

    def test_invalid_floor(self):
        self.valid_config['metadata']['floor'] = 'top'
        result = validate_full_config(self.valid_config)
        self.assertEqual(result, 'Invalid floor, must be integer')

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


# Test custom management commands used to import/export config files
class ManagementCommandTests(TestCaseBackupRestore):
    def setUp(self):
        # Create 3 test nodes, save references
        create_test_nodes()
        self.config1 = Config.objects.get(config=test_config_1)
        self.config2 = Config.objects.get(config=test_config_2)
        self.config3 = Config.objects.get(config=test_config_3)

        # Write all config files to disk
        self.config1.write_to_disk()
        self.config2.write_to_disk()
        self.config3.write_to_disk()

        # Create buffer to capture stdio from management command
        self.output = StringIO()

        # Save path to cli_config.json
        self.cli_config_path = os.path.join(settings.REPO_DIR, 'CLI', 'cli_config.json')

    def tearDown(self):
        # Remove test configs from disk
        clean_up_test_nodes()

    def test_import_configs_from_disk(self):
        # Overwrite all 3 configs in database (also overwrites on disk)
        self.config1.config = {'test': 'placeholder'}
        self.config1.save()
        self.assertNotEqual(self.config1.config, test_config_1)
        self.config2.config = {'test': 'placeholder'}
        self.config2.save()
        self.assertNotEqual(self.config2.config, test_config_2)
        self.config3.config = {'test': 'placeholder'}
        self.config3.save()
        self.assertNotEqual(self.config3.config, test_config_3)

        # Overwrite new configs on disk with original contents
        with open(os.path.join(settings.CONFIG_DIR, 'test1.json'), 'w') as file:
            json.dump(test_config_1, file)
        with open(os.path.join(settings.CONFIG_DIR, 'test2.json'), 'w') as file:
            json.dump(test_config_2, file)
        with open(os.path.join(settings.CONFIG_DIR, 'test3.json'), 'w') as file:
            json.dump(test_config_3, file)

        # Call command, confirm correct output
        call_command("import_configs_from_disk", stdout=self.output)
        self.assertIn("Importing test1.json", self.output.getvalue())
        self.assertIn("Importing test2.json", self.output.getvalue())
        self.assertIn("Importing test3.json", self.output.getvalue())

        # Confirm all configs restored in database
        self.config1.refresh_from_db()
        self.config2.refresh_from_db()
        self.config3.refresh_from_db()
        self.assertEqual(self.config1.config, test_config_1)
        self.assertEqual(self.config2.config, test_config_2)
        self.assertEqual(self.config3.config, test_config_3)

    def test_export_configs_to_disk(self):
        # Delete all 3 config files from disk
        for i in range(1, 4):
            os.remove(os.path.join(settings.CONFIG_DIR, f'test{i}.json'))
            self.assertFalse(os.path.exists(os.path.join(settings.CONFIG_DIR, f'test{i}.json')))

        # Call command, confirm correct output
        call_command("export_configs_to_disk", stdout=self.output)
        self.assertIn("Exporting test1.json", self.output.getvalue())
        self.assertIn("Exporting test2.json", self.output.getvalue())
        self.assertIn("Exporting test3.json", self.output.getvalue())

        # Confirm configs created on disk
        self.assertTrue(os.path.exists(os.path.join(settings.CONFIG_DIR, 'test1.json')))
        self.assertTrue(os.path.exists(os.path.join(settings.CONFIG_DIR, 'test2.json')))
        self.assertTrue(os.path.exists(os.path.join(settings.CONFIG_DIR, 'test3.json')))

        # Confirm config contents correct
        with open(os.path.join(settings.CONFIG_DIR, 'test1.json'), 'r') as file:
            self.assertEqual(json.load(file), test_config_1)
        with open(os.path.join(settings.CONFIG_DIR, 'test2.json'), 'r') as file:
            self.assertEqual(json.load(file), test_config_2)
        with open(os.path.join(settings.CONFIG_DIR, 'test3.json'), 'r') as file:
            self.assertEqual(json.load(file), test_config_3)

    def test_generate_cli_config(self):
        # Delete cli_config.json, confirm does not exist
        os.remove(self.cli_config_path)
        self.assertFalse(os.path.exists(self.cli_config_path))

        # Call command, confirm correct output, confirm created on disk
        call_command("generate_cli_config", stdout=self.output)
        self.assertIn("Generated config:", self.output.getvalue())
        self.assertTrue(os.path.exists(self.cli_config_path))

        # Read config from disk, confirm correct contents
        with open(self.cli_config_path) as file:
            config = json.load(file)
            # Confirm number of nodes and keywords, config dir, webrepl password
            self.assertEqual(len(config['nodes']), 3)
            self.assertEqual(len(config['schedule_keywords']), 2)
            self.assertEqual(config['config_directory'], settings.CONFIG_DIR)
            self.assertEqual(config['webrepl_password'], settings.NODE_PASSWD)

            # Confirm correct IP and config path for each node
            self.assertEqual(config['nodes']['test1']['ip'], '192.168.1.123')
            self.assertEqual(config['nodes']['test2']['ip'], '192.168.1.124')
            self.assertEqual(config['nodes']['test3']['ip'], '192.168.1.125')
            self.assertEqual(
                config['nodes']['test1']['config'],
                os.path.join(settings.CONFIG_DIR, 'test1.json')
            )
            self.assertEqual(
                config['nodes']['test2']['config'],
                os.path.join(settings.CONFIG_DIR, 'test2.json')
            )
            self.assertEqual(
                config['nodes']['test3']['config'],
                os.path.join(settings.CONFIG_DIR, 'test3.json')
            )

            # Confirm correct name and timestamp for each keyword
            self.assertEqual(config['schedule_keywords']['sunrise'], '06:00')
            self.assertEqual(config['schedule_keywords']['sunset'], '18:00')

    def test_cli_sync_disabled(self):
        # Disable CLI_SYNC
        settings.CLI_SYNC = False

        # Confirm all commands raise correct error
        with self.assertRaises(CommandError):
            call_command("export_configs_to_disk", stdout=self.output)
            self.assertIn(
                'Files cannot be written in diskless mode, set the CLI_SYNC env var to enable.',
                self.output.getvalue()
            )

        with self.assertRaises(CommandError):
            call_command("import_configs_from_disk", stdout=self.output)
            self.assertIn(
                'Files cannot be read in diskless mode, set the CLI_SYNC env var to enable.',
                self.output.getvalue()
            )

        with self.assertRaises(CommandError):
            call_command("generate_cli_config", stdout=self.output)
            self.assertIn(
                'Files cannot be written in diskless mode, set the CLI_SYNC env var to enable.',
                self.output.getvalue()
            )

        # Revert
        settings.CLI_SYNC = True
