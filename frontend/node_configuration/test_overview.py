import os
import json
from copy import deepcopy
from unittest.mock import patch
from django.conf import settings
from .views import get_modules, provision
from .models import Config, Node, ScheduleKeyword
from Webrepl import Webrepl

# Functions used to manage cli_config.json
from helper_functions import get_cli_config, remove_node_from_cli_config, load_unit_test_config

# Large JSON objects, helper functions
from .unit_test_helpers import (
    TestCaseBackupRestore,
    JSONClient,
    request_payload,
    create_test_nodes,
    clean_up_test_nodes,
    test_config_1,
    simulate_reupload_all_partial_success,
    simulate_corrupt_filesystem_upload,
    simulate_reupload_all_fail_for_different_reasons
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


# Test main overview page
class OverviewPageTests(TestCaseBackupRestore):
    def test_overview_page_no_nodes(self):
        # Request page, confirm correct template used
        response = self.client.get('/config_overview')
        self.assertTemplateUsed(response, 'node_configuration/overview.html')

        # Confirm correct context (empty)
        self.assertEqual(response.context['not_uploaded'], [])
        self.assertEqual(response.context['uploaded'], [])
        self.assertEqual(response.context['schedule_keywords'], [])

    def test_overview_page_with_nodes(self):
        # Create 3 test nodes
        create_test_nodes()

        # Request page, confirm correct template used
        response = self.client.get('/config_overview')
        self.assertTemplateUsed(response, 'node_configuration/overview.html')

        # Confirm correct context (no configs, 3 nodes, no schedule keywords)
        self.assertEqual(response.context['not_uploaded'], [])
        self.assertEqual(len(response.context['uploaded']), 3)
        self.assertEqual(response.context['schedule_keywords'], [])

        # Confirm correct node details
        self.assertEqual(
            response.context['uploaded'],
            [
                {
                    "friendly_name": "Test1",
                    "ip": "192.168.1.123",
                    "filename": "test1.json"
                },
                {
                    "friendly_name": "Test2",
                    "ip": "192.168.1.124",
                    "filename": "test2.json"
                },
                {
                    "friendly_name": "Test3",
                    "ip": "192.168.1.125",
                    "filename": "test3.json"
                }
            ]
        )

        # Remove test configs from disk
        clean_up_test_nodes()

    def test_overview_page_with_configs(self):
        # Create test config that hasn't been uploaded
        Config.objects.create(config=test_config_1, filename='test1.json')

        # Rquest page, confirm correct template used
        response = self.client.get('/config_overview')
        self.assertTemplateUsed(response, 'node_configuration/overview.html')

        # Confirm correct context (1 config, no nodes, no schedule keywords)
        self.assertEqual(len(response.context['not_uploaded']), 1)
        self.assertEqual(response.context['not_uploaded'][0]['filename'], 'test1.json')
        self.assertEqual(response.context['uploaded'], [])
        self.assertEqual(response.context['schedule_keywords'], [])

        # Confirm correct config details
        self.assertEqual(
            response.context['not_uploaded'],
            [
                {
                    "friendly_name": "Test1",
                    "filename": "test1.json"
                }
            ]
        )

    def test_overview_page_with_schedule_keywords(self):
        # Create test keywords
        ScheduleKeyword.objects.create(keyword='morning', timestamp='08:00')
        ScheduleKeyword.objects.create(keyword='sleep', timestamp='23:00')

        # Rquest page, confirm correct template used
        response = self.client.get('/config_overview')
        self.assertTemplateUsed(response, 'node_configuration/overview.html')

        # Confirm correct context (no configs, no nodes, 2 schedule keywords)
        self.assertEqual(response.context['not_uploaded'], [])
        self.assertEqual(response.context['uploaded'], [])
        self.assertEqual(len(response.context['schedule_keywords']), 2)
        self.assertEqual(response.context['schedule_keywords'][0]['keyword'], 'morning')
        self.assertEqual(response.context['schedule_keywords'][1]['keyword'], 'sleep')

    def test_overview_page_direct_connection(self):
        # Simulate direct request to backend
        response = self.client.get('/config_overview', REMOTE_ADDR='192.168.1.251')

        # Confirm correct status, context contains mocked IP
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['client_ip'], '192.168.1.251')

    def test_overview_page_proxy_connection(self):
        # Simulate request to backend through reverse proxy
        # REMOTE_ADDR is proxy host, FORWARDED_FOR is client
        response = self.client.get(
            '/config_overview',
            REMOTE_ADDR='192.168.1.100',
            HTTP_X_FORWARDED_FOR='192.168.1.251'
        )

        # Confirm correct status, context contains client IP
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['client_ip'], '192.168.1.251')


# Test delete config
class DeleteConfigTests(TestCaseBackupRestore):
    def setUp(self):
        # Set default content_type for post requests (avoid long lines)
        self.client = JSONClient()

        # Generate Config, will be deleted below
        response = self.client.post('/generate_config_file', request_payload)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(os.path.exists(os.path.join(settings.CONFIG_DIR, 'unit-test-config.json')))

    def test_delete_existing_config(self):
        # Confirm starting condition
        self.assertEqual(len(Config.objects.all()), 1)

        # Delete Config created in setUp, confirm response, confirm removed from database + disk
        response = self.client.post('/delete_config', json.dumps('unit-test-config.json'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['message'], 'Deleted unit-test-config.json')
        self.assertEqual(len(Config.objects.all()), 0)
        self.assertFalse(os.path.exists(os.path.join(settings.CONFIG_DIR, 'unit-test-config.json')))

    def test_delete_non_existing_config(self):
        # Confirm starting condition
        self.assertEqual(len(Config.objects.all()), 1)

        # Attempt to delete non-existing Config, confirm fails with correct message
        response = self.client.post('/delete_config', json.dumps('does-not-exist.json'))
        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.json()['message'],
            'Failed to delete does-not-exist.json, does not exist'
        )

        # Confirm Config still exists
        self.assertEqual(len(Config.objects.all()), 1)
        self.assertTrue(os.path.exists(os.path.join(settings.CONFIG_DIR, 'unit-test-config.json')))

    def test_delete_invalid_permission(self):
        # Confirm starting condition
        self.assertEqual(len(Config.objects.all()), 1)

        # Mock file with read-only file permissions
        with patch('os.remove', side_effect=PermissionError):
            # Attempt to delete, confirm fails with permission denied error
            response = self.client.post('/delete_config', json.dumps('unit-test-config.json'))
            self.assertEqual(response.status_code, 500)
            self.assertEqual(
                response.json()['message'],
                'Failed to delete, permission denied. This will break other features, check your filesystem permissions.'
            )

        # Confirm Config still exists
        self.assertEqual(len(Config.objects.all()), 1)
        self.assertTrue(os.path.exists(os.path.join(settings.CONFIG_DIR, 'unit-test-config.json')))

    # Original bug: Frontend threw error when attempting to delete a config that was already
    # deleted from disk, preventing the model entry from being removed. Now catches error,
    # deletes model entry, and returns normal response message.
    def test_regression_deleted_from_disk(self):
        # Delete config file, confirm still exists in database but not on disk
        os.remove(os.path.join(settings.CONFIG_DIR, 'unit-test-config.json'))
        self.assertFalse(os.path.exists(os.path.join(settings.CONFIG_DIR, 'unit-test-config.json')))
        self.assertEqual(len(Config.objects.all()), 1)

        # Simulate deleting through frontend, confirm normal response, confirm removed from database
        response = self.client.post('/delete_config', json.dumps('unit-test-config.json'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['message'], 'Deleted unit-test-config.json')
        self.assertEqual(len(Config.objects.all()), 0)
        self.assertFalse(os.path.exists(os.path.join(settings.CONFIG_DIR, 'unit-test-config.json')))

    # Original bug: The delete_config endpoint did not check if the config had
    # a Node reverse relation. If the user created a new config with the same
    # friendly name as an existing node and then clicked "Overwrite" in the
    # duplicate warning modal (calls delete_config, not delete_node) this would
    # result in a Node with no config and prevent the overview from loading.
    def test_regression_delete_config_with_associated_node(self):
        # Create Node, add Config (created in setUp) reverse relation
        node = Node.objects.create(friendly_name="Test Node", ip="192.168.1.123", floor="5")
        config = Config.objects.all()[0]
        config.node = node
        config.save()

        # Confirm 1 node and 1 config exist
        self.assertEqual(len(Node.objects.all()), 1)
        self.assertEqual(len(Config.objects.all()), 1)

        # Delete config, confirm correct response
        response = self.client.post('/delete_config', json.dumps('unit-test-config.json'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['message'], 'Deleted unit-test-config.json')

        # Confirm both models were deleted, not just config
        self.assertEqual(len(Node.objects.all()), 0)
        self.assertEqual(len(Config.objects.all()), 0)


class DeleteNodeTests(TestCaseBackupRestore):
    def setUp(self):
        # Set default content_type for post requests (avoid long lines)
        self.client = JSONClient()

        # Generate Config for test Node
        response = self.client.post('/generate_config_file', request_payload)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(os.path.exists(os.path.join(settings.CONFIG_DIR, 'unit-test-config.json')))

        # Create Node, add Config reverse relation
        self.node = Node.objects.create(friendly_name="Test Node", ip="192.168.1.123", floor="5")
        self.config = Config.objects.all()[0]
        self.config.node = self.node
        self.config.save()

    def test_delete_existing_node(self):
        # Confirm node exists in database and cli_config.json
        self.assertEqual(len(Config.objects.all()), 1)
        self.assertEqual(len(Node.objects.all()), 1)
        cli_config = get_cli_config()
        self.assertIn('test-node', cli_config['nodes'].keys())

        # Delete the Node created in setUp, confirm response message
        response = self.client.post('/delete_node', json.dumps('Test Node'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['message'], 'Deleted Test Node')

        # Confirm removed from database, disk, and cli_config.json
        self.assertEqual(len(Config.objects.all()), 0)
        self.assertEqual(len(Node.objects.all()), 0)
        self.assertFalse(os.path.exists(os.path.join(settings.CONFIG_DIR, 'unit-test-config.json')))
        cli_config = get_cli_config()
        self.assertNotIn('test-node', cli_config['nodes'].keys())

    def test_delete_non_existing_node(self):
        # Confirm starting conditions
        self.assertEqual(len(Config.objects.all()), 1)
        self.assertEqual(len(Node.objects.all()), 1)

        # Attempt to delete non-existing Node, confirm fails with correct message
        response = self.client.post('/delete_node', json.dumps('Wrong Node'))
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()['message'], 'Failed to delete Wrong Node, does not exist')

        # Confirm Node and Config still exist
        self.assertEqual(len(Config.objects.all()), 1)
        self.assertEqual(len(Node.objects.all()), 1)
        self.assertTrue(os.path.exists(os.path.join(settings.CONFIG_DIR, 'unit-test-config.json')))

    def test_delete_invalid_permission(self):
        # Confirm starting conditions
        self.assertEqual(len(Config.objects.all()), 1)
        self.assertEqual(len(Node.objects.all()), 1)

        # Mock file with read-only file permissions
        with patch('os.remove', side_effect=PermissionError):
            # Attempt to delete, confirm fails with permission denied error
            response = self.client.post('/delete_node', json.dumps('Test Node'))
            self.assertEqual(response.status_code, 500)
            self.assertEqual(
                response.json()['message'],
                'Failed to delete, permission denied. This will break other features, check your filesystem permissions.'
            )

        # Confirm Node and Config still exist
        self.assertEqual(len(Config.objects.all()), 1)
        self.assertEqual(len(Node.objects.all()), 1)
        self.assertTrue(os.path.exists(os.path.join(settings.CONFIG_DIR, 'unit-test-config.json')))

    # Original bug: Impossible to delete node if config file deleted
    # from disk, traceback when file not found. Fixed in 1af01a00.
    def test_regression_delete_node_config_not_on_disk(self):
        # Delete config from disk but not database, confirm removed
        os.remove(os.path.join(settings.CONFIG_DIR, 'unit-test-config.json'))
        self.assertFalse(os.path.exists(os.path.join(settings.CONFIG_DIR, 'unit-test-config.json')))
        self.assertEqual(len(Config.objects.all()), 1)
        self.assertEqual(len(Node.objects.all()), 1)

        # Delete Node, should ignore missing file on disk
        response = self.client.post('/delete_node', json.dumps('Test Node'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['message'], 'Deleted Test Node')
        self.assertEqual(len(Config.objects.all()), 0)
        self.assertEqual(len(Node.objects.all()), 0)
        self.assertFalse(os.path.exists(os.path.join(settings.CONFIG_DIR, 'unit-test-config.json')))


# Test endpoint called by frontend upload buttons (calls get_modules and provision)
class UploadTests(TestCaseBackupRestore):
    def setUp(self):
        # Set default content_type for post requests (avoid long lines)
        self.client = JSONClient()

    def test_upload_new_node(self):
        # Create test config, confirm added to database
        Config.objects.create(config=test_config_1, filename='test1.json')
        self.assertEqual(len(Config.objects.all()), 1)

        # Confirm no nodes in database or cli_config.json
        self.assertEqual(len(Node.objects.all()), 0)
        remove_node_from_cli_config('Test1')

        # Mock Webrepl to return True without doing anything
        with patch.object(Webrepl, 'open_connection', return_value=True), \
             patch.object(Webrepl, 'put_file', return_value=True), \
             patch.object(Webrepl, 'put_file_mem', return_value=True):

            # Upload config, verify response
            response = self.client.post(
                '/upload',
                {'config': 'test1.json', 'ip': '123.45.67.89'}
            )
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()['message'], 'Upload complete.')

        # Should create 1 Node, no configs
        self.assertEqual(len(Config.objects.all()), 1)
        self.assertEqual(len(Node.objects.all()), 1)
        self.assertTrue(Node.objects.get(friendly_name='Test1'))

        # Should exist in cli_config.json
        cli_config = get_cli_config()
        self.assertIn('test1', cli_config['nodes'].keys())
        self.assertEqual(cli_config['nodes']['test1']['ip'], '123.45.67.89')
        self.assertEqual(
            cli_config['nodes']['test1']['config'],
            os.path.join(settings.CONFIG_DIR, 'test1.json')
        )

    def test_reupload_existing(self):
        # Create test config, confirm database
        create_test_nodes()
        self.assertEqual(len(Config.objects.all()), 3)
        self.assertEqual(len(Node.objects.all()), 3)

        # Mock Webrepl to return True without doing anything
        with patch.object(Webrepl, 'open_connection', return_value=True), \
             patch.object(Webrepl, 'put_file', return_value=True), \
             patch.object(Webrepl, 'put_file_mem', return_value=True):

            # Reupload config (second URL parameter), verify response
            response = self.client.post(
                '/upload/True',
                {'config': 'test1.json', 'ip': '123.45.67.89'}
            )
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()['message'], 'Upload complete.')

        # Should have same number of configs and nodes
        self.assertEqual(len(Config.objects.all()), 3)
        self.assertEqual(len(Node.objects.all()), 3)

        # Remove test configs from disk
        clean_up_test_nodes()

    def test_upload_non_existing_config(self):
        # Confirm database empty
        self.assertEqual(len(Config.objects.all()), 0)
        self.assertEqual(len(Node.objects.all()), 0)

        # Mock Webrepl to return True without doing anything
        with patch.object(Webrepl, 'open_connection', return_value=True), \
             patch.object(Webrepl, 'put_file', return_value=True):

            # Reupload config (second URL parameter), verify error
            response = self.client.post(
                '/upload',
                {'config': 'fake-config.json', 'ip': '123.45.67.89'}
            )
            self.assertEqual(response.status_code, 404)
            self.assertEqual(
                response.json()['message'],
                "Config file doesn't exist - did you delete it manually?"
            )

        # Database should still be empty
        self.assertEqual(len(Config.objects.all()), 0)
        self.assertEqual(len(Node.objects.all()), 0)

    def test_upload_to_offline_node(self):
        # Create test config, confirm database
        Config.objects.create(config=test_config_1, filename='test1.json')
        self.assertEqual(len(Config.objects.all()), 1)
        self.assertEqual(len(Node.objects.all()), 0)

        # Mock Webrepl to fail to connect
        with patch.object(Webrepl, 'open_connection', return_value=False):

            # Upload config, verify error
            response = self.client.post(
                '/upload',
                {'config': 'test1.json', 'ip': '123.45.67.89'}
            )
            self.assertEqual(response.status_code, 404)
            self.assertEqual(
                response.json()['message'],
                'Error: Unable to connect to node, please make sure it is connected to wifi and try again.'
            )

        # Should not create Node or Config
        self.assertEqual(len(Config.objects.all()), 1)
        self.assertEqual(len(Node.objects.all()), 0)
        with self.assertRaises(Node.DoesNotExist):
            Node.objects.get(friendly_name='Test1')

    def test_upload_connection_timeout(self):
        # Create test config, confirm database
        Config.objects.create(config=test_config_1, filename='test1.json')
        self.assertEqual(len(Config.objects.all()), 1)
        self.assertEqual(len(Node.objects.all()), 0)

        # Mock Webrepl.put_file to raise TimeoutError
        with patch.object(Webrepl, 'open_connection', return_value=True), \
             patch.object(Webrepl, 'put_file_mem', side_effect=TimeoutError):

            response = self.client.post(
                '/upload',
                {'config': 'test1.json', 'ip': '123.45.67.89'}
            )
            self.assertEqual(response.status_code, 408)
            self.assertEqual(
                response.json()['message'],
                'Connection timed out - please press target node reset button, wait 30 seconds, and try again.'
            )

        # Should not create Node or Config
        self.assertEqual(len(Config.objects.all()), 1)
        self.assertEqual(len(Node.objects.all()), 0)
        with self.assertRaises(Node.DoesNotExist):
            Node.objects.get(friendly_name='Test1')

    # Verify correct error when passed an invalid IP
    def test_invalid_ip(self):
        response = self.client.post('/upload', {'ip': '123.456.678.90'})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['message'], 'Invalid IP 123.456.678.90')


# Test view that uploads completed configs and dependencies to esp32 nodes
class ProvisionTests(TestCaseBackupRestore):
    def test_provision(self):
        modules = get_modules(test_config_1, settings.REPO_DIR)

        # Mock Webrepl to return True without doing anything
        with patch.object(Webrepl, 'open_connection', return_value=True), \
             patch.object(Webrepl, 'put_file', return_value=True), \
             patch.object(Webrepl, 'put_file_mem', return_value=True):

            response = provision('123.45.67.89', 'password', 'test1.json', modules)
            self.assertEqual(response['status'], 200)
            self.assertEqual(response['message'], "Upload complete.")

    def test_provision_offline_node(self):
        modules = get_modules(test_config_1, settings.REPO_DIR)

        # Mock Webrepl to fail to connect
        with patch.object(Webrepl, 'open_connection', return_value=False):

            response = provision('123.45.67.89', 'password', 'test1.json', modules)
            self.assertEqual(response['status'], 404)
            self.assertEqual(
                response['message'],
                'Error: Unable to connect to node, please make sure it is connected to wifi and try again.'
            )

    def test_provision_connection_timeout(self):
        modules = get_modules(test_config_1, settings.REPO_DIR)

        # Mock Webrepl.put_file to raise TimeoutError
        with patch.object(Webrepl, 'open_connection', return_value=True), \
             patch.object(Webrepl, 'put_file_mem', side_effect=TimeoutError):

            response = provision('123.45.67.89', 'password', 'test1.json', modules)
            self.assertEqual(response['status'], 408)
            self.assertEqual(
                response['message'],
                'Connection timed out - please press target node reset button, wait 30 seconds, and try again.'
            )

    def test_provision_corrupt_filesystem(self):
        modules = get_modules(test_config_1, settings.REPO_DIR)

        # Mock Webrepl.put_file to raise AssertionError for non-library files
        # (simulates failing to upload to root dir)
        with patch.object(Webrepl, 'open_connection', return_value=True), \
             patch.object(Webrepl, 'put_file_mem', new=simulate_corrupt_filesystem_upload):

            response = provision('123.45.67.89', 'password', 'test1.json', modules)
            self.assertEqual(response['status'], 409)
            self.assertEqual(
                response['message'],
                'Failed due to filesystem error, please re-flash firmware.'
            )


# Test function that takes config file, returns list of dependencies for upload
class GetModulesTests(TestCaseBackupRestore):
    def setUp(self):
        self.config = load_unit_test_config()

    def test_get_modules_full_config(self):

        expected_modules = {
            os.path.join(settings.REPO_DIR, 'devices', 'ApiTarget.py'): 'ApiTarget.py',
            os.path.join(settings.REPO_DIR, 'devices', 'Wled.py'): 'Wled.py',
            os.path.join(settings.REPO_DIR, 'devices', 'Mosfet.py'): 'Mosfet.py',
            os.path.join(settings.REPO_DIR, 'devices', 'TasmotaRelay.py'): 'TasmotaRelay.py',
            os.path.join(settings.REPO_DIR, 'sensors', 'MotionSensor.py'): 'MotionSensor.py',
            os.path.join(settings.REPO_DIR, 'sensors', 'Dummy.py'): 'Dummy.py',
            os.path.join(settings.REPO_DIR, 'devices', 'Device.py'): 'Device.py',
            os.path.join(settings.REPO_DIR, 'sensors', 'Switch.py'): 'Switch.py',
            os.path.join(settings.REPO_DIR, 'sensors', 'Desktop_trigger.py'): 'Desktop_trigger.py',
            os.path.join(settings.REPO_DIR, 'devices', 'DumbRelay.py'): 'DumbRelay.py',
            os.path.join(settings.REPO_DIR, 'devices', 'Tplink.py'): 'Tplink.py',
            os.path.join(settings.REPO_DIR, 'devices', 'Desktop_target.py'): 'Desktop_target.py',
            os.path.join(settings.REPO_DIR, 'sensors', 'Thermostat.py'): 'Thermostat.py',
            os.path.join(settings.REPO_DIR, 'sensors', 'Si7021.py'): 'Si7021.py',
            os.path.join(settings.REPO_DIR, 'sensors', 'Sensor.py'): 'Sensor.py',
            os.path.join(settings.REPO_DIR, 'devices', 'LedStrip.py'): 'LedStrip.py',
            os.path.join(settings.REPO_DIR, 'devices', 'DimmableLight.py'): 'DimmableLight.py',
            os.path.join(settings.REPO_DIR, 'devices', 'HttpGet.py'): 'HttpGet.py',
            os.path.join(settings.REPO_DIR, 'devices', 'IrBlaster.py'): 'IrBlaster.py',
            os.path.join(settings.REPO_DIR, 'core', 'Instance.py'): 'Instance.py',
            os.path.join(settings.REPO_DIR, 'core', 'Config.py'): 'Config.py',
            os.path.join(settings.REPO_DIR, 'core', 'Group.py'): 'Group.py',
            os.path.join(settings.REPO_DIR, 'core', 'SoftwareTimer.py'): 'SoftwareTimer.py',
            os.path.join(settings.REPO_DIR, 'core', 'Api.py'): 'Api.py',
            os.path.join(settings.REPO_DIR, 'core', 'util.py'): 'util.py',
            os.path.join(settings.REPO_DIR, 'core', 'main.py'): 'main.py'
        }

        modules = get_modules(self.config, settings.REPO_DIR)
        self.assertEqual(modules, expected_modules)

    def test_get_modules_empty_config(self):
        expected_modules = {
            os.path.join(settings.REPO_DIR, 'core', 'Config.py'): 'Config.py',
            os.path.join(settings.REPO_DIR, 'core', 'Group.py'): 'Group.py',
            os.path.join(settings.REPO_DIR, 'core', 'SoftwareTimer.py'): 'SoftwareTimer.py',
            os.path.join(settings.REPO_DIR, 'core', 'Api.py'): 'Api.py',
            os.path.join(settings.REPO_DIR, 'core', 'util.py'): 'util.py',
            os.path.join(settings.REPO_DIR, 'core', 'main.py'): 'main.py'
        }

        # Should only return core modules, no devices or sensors
        modules = get_modules({}, settings.REPO_DIR)
        self.assertEqual(modules, expected_modules)

    def test_get_modules_no_ir_blaster(self):
        del self.config['ir_blaster']

        expected_modules = {
            os.path.join(settings.REPO_DIR, 'devices', 'ApiTarget.py'): 'ApiTarget.py',
            os.path.join(settings.REPO_DIR, 'devices', 'Wled.py'): 'Wled.py',
            os.path.join(settings.REPO_DIR, 'devices', 'Mosfet.py'): 'Mosfet.py',
            os.path.join(settings.REPO_DIR, 'devices', 'TasmotaRelay.py'): 'TasmotaRelay.py',
            os.path.join(settings.REPO_DIR, 'sensors', 'MotionSensor.py'): 'MotionSensor.py',
            os.path.join(settings.REPO_DIR, 'sensors', 'Dummy.py'): 'Dummy.py',
            os.path.join(settings.REPO_DIR, 'devices', 'Device.py'): 'Device.py',
            os.path.join(settings.REPO_DIR, 'sensors', 'Switch.py'): 'Switch.py',
            os.path.join(settings.REPO_DIR, 'sensors', 'Desktop_trigger.py'): 'Desktop_trigger.py',
            os.path.join(settings.REPO_DIR, 'devices', 'DumbRelay.py'): 'DumbRelay.py',
            os.path.join(settings.REPO_DIR, 'devices', 'Tplink.py'): 'Tplink.py',
            os.path.join(settings.REPO_DIR, 'devices', 'Desktop_target.py'): 'Desktop_target.py',
            os.path.join(settings.REPO_DIR, 'sensors', 'Thermostat.py'): 'Thermostat.py',
            os.path.join(settings.REPO_DIR, 'sensors', 'Si7021.py'): 'Si7021.py',
            os.path.join(settings.REPO_DIR, 'sensors', 'Sensor.py'): 'Sensor.py',
            os.path.join(settings.REPO_DIR, 'devices', 'LedStrip.py'): 'LedStrip.py',
            os.path.join(settings.REPO_DIR, 'devices', 'DimmableLight.py'): 'DimmableLight.py',
            os.path.join(settings.REPO_DIR, 'devices', 'HttpGet.py'): 'HttpGet.py',
            os.path.join(settings.REPO_DIR, 'core', 'Instance.py'): 'Instance.py',
            os.path.join(settings.REPO_DIR, 'core', 'Config.py'): 'Config.py',
            os.path.join(settings.REPO_DIR, 'core', 'Group.py'): 'Group.py',
            os.path.join(settings.REPO_DIR, 'core', 'SoftwareTimer.py'): 'SoftwareTimer.py',
            os.path.join(settings.REPO_DIR, 'core', 'Api.py'): 'Api.py',
            os.path.join(settings.REPO_DIR, 'core', 'util.py'): 'util.py',
            os.path.join(settings.REPO_DIR, 'core', 'main.py'): 'main.py'
        }

        modules = get_modules(self.config, settings.REPO_DIR)
        self.assertEqual(modules, expected_modules)

    def test_get_modules_no_thermostat(self):
        del self.config['sensor5']

        expected_modules = {
            os.path.join(settings.REPO_DIR, 'devices', 'ApiTarget.py'): 'ApiTarget.py',
            os.path.join(settings.REPO_DIR, 'devices', 'Wled.py'): 'Wled.py',
            os.path.join(settings.REPO_DIR, 'devices', 'Mosfet.py'): 'Mosfet.py',
            os.path.join(settings.REPO_DIR, 'devices', 'TasmotaRelay.py'): 'TasmotaRelay.py',
            os.path.join(settings.REPO_DIR, 'sensors', 'MotionSensor.py'): 'MotionSensor.py',
            os.path.join(settings.REPO_DIR, 'sensors', 'Dummy.py'): 'Dummy.py',
            os.path.join(settings.REPO_DIR, 'devices', 'Device.py'): 'Device.py',
            os.path.join(settings.REPO_DIR, 'sensors', 'Switch.py'): 'Switch.py',
            os.path.join(settings.REPO_DIR, 'sensors', 'Desktop_trigger.py'): 'Desktop_trigger.py',
            os.path.join(settings.REPO_DIR, 'devices', 'DumbRelay.py'): 'DumbRelay.py',
            os.path.join(settings.REPO_DIR, 'devices', 'Tplink.py'): 'Tplink.py',
            os.path.join(settings.REPO_DIR, 'devices', 'Desktop_target.py'): 'Desktop_target.py',
            os.path.join(settings.REPO_DIR, 'sensors', 'Sensor.py'): 'Sensor.py',
            os.path.join(settings.REPO_DIR, 'devices', 'LedStrip.py'): 'LedStrip.py',
            os.path.join(settings.REPO_DIR, 'devices', 'DimmableLight.py'): 'DimmableLight.py',
            os.path.join(settings.REPO_DIR, 'devices', 'HttpGet.py'): 'HttpGet.py',
            os.path.join(settings.REPO_DIR, 'devices', 'IrBlaster.py'): 'IrBlaster.py',
            os.path.join(settings.REPO_DIR, 'core', 'Instance.py'): 'Instance.py',
            os.path.join(settings.REPO_DIR, 'core', 'Config.py'): 'Config.py',
            os.path.join(settings.REPO_DIR, 'core', 'Group.py'): 'Group.py',
            os.path.join(settings.REPO_DIR, 'core', 'SoftwareTimer.py'): 'SoftwareTimer.py',
            os.path.join(settings.REPO_DIR, 'core', 'Api.py'): 'Api.py',
            os.path.join(settings.REPO_DIR, 'core', 'util.py'): 'util.py',
            os.path.join(settings.REPO_DIR, 'core', 'main.py'): 'main.py'
        }

        modules = get_modules(self.config, settings.REPO_DIR)
        self.assertEqual(modules, expected_modules)

    def test_get_modules_realistic(self):
        del self.config['ir_blaster']
        del self.config['sensor3']
        del self.config['sensor4']
        del self.config['sensor5']
        del self.config['device4']
        del self.config['device5']
        del self.config['device7']

        expected_modules = {
            os.path.join(settings.REPO_DIR, 'devices', 'ApiTarget.py'): 'ApiTarget.py',
            os.path.join(settings.REPO_DIR, 'devices', 'TasmotaRelay.py'): 'TasmotaRelay.py',
            os.path.join(settings.REPO_DIR, 'sensors', 'MotionSensor.py'): 'MotionSensor.py',
            os.path.join(settings.REPO_DIR, 'devices', 'Device.py'): 'Device.py',
            os.path.join(settings.REPO_DIR, 'sensors', 'Switch.py'): 'Switch.py',
            os.path.join(settings.REPO_DIR, 'devices', 'Tplink.py'): 'Tplink.py',
            os.path.join(settings.REPO_DIR, 'devices', 'Wled.py'): 'Wled.py',
            os.path.join(settings.REPO_DIR, 'sensors', 'Sensor.py'): 'Sensor.py',
            os.path.join(settings.REPO_DIR, 'devices', 'LedStrip.py'): 'LedStrip.py',
            os.path.join(settings.REPO_DIR, 'devices', 'DimmableLight.py'): 'DimmableLight.py',
            os.path.join(settings.REPO_DIR, 'devices', 'HttpGet.py'): 'HttpGet.py',
            os.path.join(settings.REPO_DIR, 'core', 'Instance.py'): 'Instance.py',
            os.path.join(settings.REPO_DIR, 'core', 'Config.py'): 'Config.py',
            os.path.join(settings.REPO_DIR, 'core', 'Group.py'): 'Group.py',
            os.path.join(settings.REPO_DIR, 'core', 'SoftwareTimer.py'): 'SoftwareTimer.py',
            os.path.join(settings.REPO_DIR, 'core', 'Api.py'): 'Api.py',
            os.path.join(settings.REPO_DIR, 'core', 'util.py'): 'util.py',
            os.path.join(settings.REPO_DIR, 'core', 'main.py'): 'main.py'
        }

        modules = get_modules(self.config, settings.REPO_DIR)
        self.assertEqual(modules, expected_modules)


# Test view that connects to existing node, downloads config file, writes to database
class RestoreConfigViewTest(TestCaseBackupRestore):
    def setUp(self):
        # Set default content_type for post requests (avoid long lines)
        self.client = JSONClient()

    def test_restore_config(self):
        # Database should be empty, config file should not exist on disk
        self.assertEqual(len(Config.objects.all()), 0)
        self.assertEqual(len(Node.objects.all()), 0)
        if os.path.exists(os.path.join(settings.CONFIG_DIR, 'test1.json')):
            os.remove(os.path.join(settings.CONFIG_DIR, 'test1.json'))

        # Mock Webrepl to return byte-encoded test_config_1 (simulate receiving from ESP32)
        with patch.object(Webrepl, 'open_connection', return_value=True), \
             patch.object(Webrepl, 'get_file_mem', return_value=json.dumps(test_config_1).encode('utf-8')):

            # Post fake IP to endpoint, confirm output
            response = self.client.post('/restore_config', {'ip': '123.45.67.89'})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(
                response.json()['message'],
                {
                    'friendly_name': 'Test1',
                    'filename': 'test1.json',
                    'ip': '123.45.67.89'
                }
            )

        # Config and Node should now exist, config file should exist on disk
        self.assertEqual(len(Config.objects.all()), 1)
        self.assertEqual(len(Node.objects.all()), 1)
        self.assertTrue(Config.objects.get(filename='test1.json'))
        self.assertTrue(Node.objects.get(friendly_name='Test1'))
        self.assertTrue(os.path.exists(os.path.join(settings.CONFIG_DIR, 'test1.json')))

        # Config should be identical to input object
        config = Config.objects.get(filename='test1.json').config
        self.assertEqual(config, test_config_1)
        self.assertEqual(len(config['metadata']['schedule_keywords']), 2)
        self.assertIn('sunrise', config['metadata']['schedule_keywords'].keys())
        self.assertIn('sunset', config['metadata']['schedule_keywords'].keys())

    def test_target_offline(self):
        # Database should be empty
        self.assertEqual(len(Config.objects.all()), 0)
        self.assertEqual(len(Node.objects.all()), 0)

        # Mock Webrepl to fail to connect
        with patch.object(Webrepl, 'open_connection', return_value=False):

            # Post fake IP to endpoint, confirm weeoe
            response = self.client.post('/restore_config', {'ip': '123.45.67.89'})
            self.assertEqual(response.status_code, 404)
            self.assertEqual(
                response.json()['message'],
                'Unable to connect to node, please make sure it is connected to wifi and try again.'
            )

        # Database should still be empty
        self.assertEqual(len(Config.objects.all()), 0)
        self.assertEqual(len(Node.objects.all()), 0)

    def test_duplicate_config_name(self):
        # Create 3 test nodes
        create_test_nodes()
        self.assertEqual(len(Config.objects.all()), 3)
        self.assertEqual(len(Node.objects.all()), 3)

        # Mock Webrepl to return byte-encoded test_config_1 (duplicate, already used by create_test_nodes)
        with patch.object(Webrepl, 'open_connection', return_value=True), \
             patch.object(Webrepl, 'get_file_mem', return_value=json.dumps(test_config_1).encode('utf-8')):

            # Post fake IP to endpoint, confirm error
            response = self.client.post('/restore_config', {'ip': '123.45.67.89'})
            self.assertEqual(response.status_code, 409)
            self.assertEqual(
                response.json()['message'],
                'Config already exists with identical name'
            )

        # Should still have 3
        self.assertEqual(len(Config.objects.all()), 3)
        self.assertEqual(len(Node.objects.all()), 3)

        # Remove test configs from disk
        clean_up_test_nodes()

    # Verify correct error when passed an invalid IP
    def test_invalid_ip(self):
        response = self.client.post('/restore_config', {'ip': '123.456.678.90'})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['message'], 'Invalid IP 123.456.678.90')

    # Should refuse to create in database if invalid config received
    def test_invalid_config_format(self):
        # Database should be empty
        self.assertEqual(len(Config.objects.all()), 0)
        self.assertEqual(len(Node.objects.all()), 0)

        # Delete required key from config
        invalid_config = deepcopy(test_config_1)
        del invalid_config['metadata']['floor']

        # Mock Webrepl to return byte-encoded invalid config
        with patch.object(Webrepl, 'open_connection', return_value=True), \
             patch.object(Webrepl, 'get_file_mem', return_value=json.dumps(invalid_config).encode('utf-8')):

            # Post fake IP to endpoint, confirm error, confirm no models created
            response = self.client.post('/restore_config', {'ip': '123.45.67.89'})
            self.assertEqual(response.status_code, 500)
            self.assertEqual(
                response.json()['message'],
                'Config format invalid, possibly outdated version.'
            )
            self.assertEqual(len(Config.objects.all()), 0)
            self.assertEqual(len(Node.objects.all()), 0)


# Test endpoint called by reupload all option in config overview
class ReuploadAllTests(TestCaseBackupRestore):
    def setUp(self):
        create_test_nodes()

        self.failed_to_connect = {
            'message': 'Unable to connect to node, please make sure it is connected to wifi and try again.',
            'status': 404
        }

    def tearDown(self):
        # Remove test configs from disk
        clean_up_test_nodes()

    def test_reupload_all(self):
        # Mock provision to return success message without doing anything
        with patch('node_configuration.views.provision') as mock_provision:
            mock_provision.return_value = {'message': 'Upload complete.', 'status': 200}

            # Send request, validate response, validate that provision is called exactly 3 times
            response = self.client.get('/reupload_all')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(
                response.json()['message'],
                {'success': ['Test1', 'Test2', 'Test3'], 'failed': {}}
            )
            self.assertEqual(mock_provision.call_count, 3)

    def test_reupload_all_partial_success(self):
        # Mock provision to return failure message for Test2, success for everything else
        with patch('node_configuration.views.provision', new=simulate_reupload_all_partial_success):

            # Send request, validate response, validate that test1 and test3 succeeded, test2 failed
            response = self.client.get('/reupload_all')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(
                response.json()['message'],
                {'success': ['Test3'], 'failed': {'Test1': 'Unknown error', 'Test2': 'Offline'}}
            )

    def test_reupload_all_fail(self):
        # Expected response object
        all_failed = {
            "success": [],
            "failed": {
                "Test1": "Offline",
                "Test2": "Offline",
                "Test3": "Offline"
            }
        }

        # Mock provision to return failure message without doing anything
        with patch('node_configuration.views.provision', return_value=self.failed_to_connect) as mock_provision:

            # Send request, validate response, validate that provision is called exactly 3 times
            response = self.client.get('/reupload_all')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()['message'], all_failed)
            self.assertEqual(mock_provision.call_count, 3)

    def test_reupload_all_fail_different_reasons(self):
        # Expected response object
        all_failed_different_reasons = {
            "success": [],
            "failed": {
                "Test1": "Connection timed out",
                "Test2": "Offline",
                "Test3": "Filesystem error"
            }
        }

        # Mock provision to return failure message without doing anything
        with patch('node_configuration.views.provision', new=simulate_reupload_all_fail_for_different_reasons):

            # Send request, validate response, validate that provision is called exactly 3 times
            response = self.client.get('/reupload_all')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()['message'], all_failed_different_reasons)


# Test endpoint used to change an existing node's IP
class ChangeNodeIpTests(TestCaseBackupRestore):
    def setUp(self):
        # Set default content_type for post requests (avoid long lines)
        self.client = JSONClient()

        # Create 3 test nodes
        create_test_nodes()

    def tearDown(self):
        # Remove test configs from disk
        clean_up_test_nodes()

    def test_change_node_ip(self):
        # Confirm starting IP, confirm same IP in cli_config.json
        self.assertEqual(Node.objects.all()[0].ip, '192.168.1.123')
        cli_config = get_cli_config()
        self.assertEqual(cli_config['nodes']['test1']['ip'], '192.168.1.123')

        # Mock provision to return success message
        with patch('node_configuration.views.provision') as mock_provision:
            mock_provision.return_value = {'message': 'Upload complete.', 'status': 200}

            # Make request, confirm response
            request_payload = {'friendly_name': 'Test1', 'new_ip': '192.168.1.255'}
            response = self.client.post('/change_node_ip', request_payload)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()['message'], 'Successfully uploaded to new IP')

            # Confirm node model IP changed, upload was called
            self.assertEqual(Node.objects.all()[0].ip, '192.168.1.255')
            self.assertEqual(mock_provision.call_count, 1)

            # Confirm IP changed in cli_config.json
            cli_config = get_cli_config()
            self.assertEqual(cli_config['nodes']['test1']['ip'], '192.168.1.255')

    def test_target_ip_offline(self):
        # Mock provision to return failure message without doing anything
        with patch('node_configuration.views.provision') as mock_provision:
            mock_provision.return_value = {
                'message': 'Unable to connect to node, please make sure it is connected to wifi and try again.',
                'status': 404
            }

            # Make request, confirm error
            request_payload = {'friendly_name': 'Test1', 'new_ip': '192.168.1.255'}
            response = self.client.post('/change_node_ip', request_payload)
            self.assertEqual(response.status_code, 404)
            self.assertEqual(
                response.json()['message'],
                "Unable to connect to node, please make sure it is connected to wifi and try again."
            )

    def test_invalid_get_request(self):
        # Requires post, confirm errors
        response = self.client.get('/change_node_ip')
        self.assertEqual(response.status_code, 405)
        self.assertEqual(response.json()['message'], 'Must post data')

    def test_invalid_parameters(self):
        # Make request with invalid IP, confirm error
        request_payload = {'friendly_name': 'Test1', 'new_ip': '192.168.1.555'}
        response = self.client.post('/change_node_ip', request_payload)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['message'], 'Invalid IP 192.168.1.555')

        # Make request targeting non-existing node, confirm error
        request_payload = {'friendly_name': 'Test9', 'new_ip': '192.168.1.255'}
        response = self.client.post('/change_node_ip', request_payload)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()['message'], "Unable to change IP, node does not exist")

        # Make request with current IP, confirm error
        request_payload = {'friendly_name': 'Test1', 'new_ip': '192.168.1.123'}
        response = self.client.post('/change_node_ip', request_payload)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['message'], 'New IP must be different than old')
