import os
import json
from copy import deepcopy
from unittest.mock import patch
from django.conf import settings
from django.test import TestCase
from .views import get_modules, provision
from .models import Config, Node, ScheduleKeyword
from Webrepl import Webrepl
from helper_functions import load_unit_test_config
# Large JSON objects, helper functions
from .unit_test_helpers import (
    JSONClient,
    request_payload,
    create_test_nodes,
    test_config_1,
    simulate_reupload_all_partial_success,
    simulate_corrupt_filesystem_upload,
    simulate_reupload_all_fail_for_different_reasons
)


# Test main overview page
class OverviewPageTests(TestCase):
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

    def test_overview_page_with_configs(self):
        # Create test config that hasn't been uploaded
        Config.objects.create(config=test_config_1, filename='test1.json')

        # Request page, confirm correct template used
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

        # Request page, confirm correct template used
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
class DeleteConfigTests(TestCase):
    def setUp(self):
        # Set default content_type for post requests (avoid long lines)
        self.client = JSONClient()

        # Generate Config, will be deleted below
        response = self.client.post('/generate_config_file', request_payload)
        self.assertEqual(response.status_code, 200)

    def test_delete_existing_config(self):
        # Confirm starting condition
        self.assertEqual(len(Config.objects.all()), 1)

        # Delete Config created in setUp, confirm response, confirm removed from database
        response = self.client.post('/delete_config', json.dumps('unit-test-config.json'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['message'], 'Deleted unit-test-config.json')
        self.assertEqual(len(Config.objects.all()), 0)

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


class DeleteNodeTests(TestCase):
    def setUp(self):
        # Set default content_type for post requests (avoid long lines)
        self.client = JSONClient()

        # Generate Config for test Node
        response = self.client.post('/generate_config_file', request_payload)
        self.assertEqual(response.status_code, 200)

        # Create Node, add Config reverse relation
        self.node = Node.objects.create(friendly_name="Test Node", ip="192.168.1.123", floor="5")
        self.config = Config.objects.all()[0]
        self.config.node = self.node
        self.config.save()

    def test_delete_existing_node(self):
        # Confirm node exists in database
        self.assertEqual(len(Config.objects.all()), 1)
        self.assertEqual(len(Node.objects.all()), 1)

        # Delete the Node created in setUp, confirm response message
        response = self.client.post(
            '/delete_node',
            json.dumps({'friendly_name': 'Test Node'})
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['message'], 'Deleted Test Node')

        # Confirm removed from database
        self.assertEqual(len(Config.objects.all()), 0)
        self.assertEqual(len(Node.objects.all()), 0)

    def test_delete_existing_node_by_ip_address(self):
        # Confirm node exists in database
        self.assertEqual(len(Config.objects.all()), 1)
        self.assertEqual(len(Node.objects.all()), 1)

        # Delete the Node using its IP address, confirm response message
        response = self.client.post(
            '/delete_node',
            json.dumps({'ip': '192.168.1.123'})
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['message'], 'Deleted Test Node')

        # Confirm removed from database
        self.assertEqual(len(Config.objects.all()), 0)
        self.assertEqual(len(Node.objects.all()), 0)

    def test_delete_non_existing_node(self):
        # Confirm starting conditions
        self.assertEqual(len(Config.objects.all()), 1)
        self.assertEqual(len(Node.objects.all()), 1)

        # Attempt to delete non-existing Node, confirm fails with correct message
        response = self.client.post(
            '/delete_node',
            json.dumps({'friendly_name': 'Wrong Node'})
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.json()['message'],
            'Failed to delete, matching node does not exist'
        )

        # Confirm Node and Config still exist
        self.assertEqual(len(Config.objects.all()), 1)
        self.assertEqual(len(Node.objects.all()), 1)


# Test endpoint called by frontend upload buttons (calls get_modules and provision)
class UploadTests(TestCase):
    def setUp(self):
        # Set default content_type for post requests (avoid long lines)
        self.client = JSONClient()

    def test_upload_new_node(self):
        # Create test config, confirm added to database
        Config.objects.create(config=test_config_1, filename='test1.json')
        self.assertEqual(len(Config.objects.all()), 1)

        # Confirm no nodes in database
        self.assertEqual(len(Node.objects.all()), 0)

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
class ProvisionTests(TestCase):
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
class GetModulesTests(TestCase):
    def setUp(self):
        self.config = load_unit_test_config()

    def test_get_modules_full_config(self):

        expected_modules = {
            os.path.join(settings.REPO_DIR, 'devices', 'ApiTarget.py'): 'ApiTarget.py',
            os.path.join(settings.REPO_DIR, 'devices', 'Wled.py'): 'Wled.py',
            os.path.join(settings.REPO_DIR, 'devices', 'TasmotaRelay.py'): 'TasmotaRelay.py',
            os.path.join(settings.REPO_DIR, 'sensors', 'MotionSensor.py'): 'MotionSensor.py',
            os.path.join(settings.REPO_DIR, 'sensors', 'Dummy.py'): 'Dummy.py',
            os.path.join(settings.REPO_DIR, 'devices', 'Device.py'): 'Device.py',
            os.path.join(settings.REPO_DIR, 'sensors', 'Switch.py'): 'Switch.py',
            os.path.join(settings.REPO_DIR, 'sensors', 'DesktopTrigger.py'): 'DesktopTrigger.py',
            os.path.join(settings.REPO_DIR, 'devices', 'Relay.py'): 'Relay.py',
            os.path.join(settings.REPO_DIR, 'devices', 'Tplink.py'): 'Tplink.py',
            os.path.join(settings.REPO_DIR, 'devices', 'DesktopTarget.py'): 'DesktopTarget.py',
            os.path.join(settings.REPO_DIR, 'sensors', 'Thermostat.py'): 'Thermostat.py',
            os.path.join(settings.REPO_DIR, 'sensors', 'Si7021.py'): 'Si7021.py',
            os.path.join(settings.REPO_DIR, 'sensors', 'Sensor.py'): 'Sensor.py',
            os.path.join(settings.REPO_DIR, 'sensors', 'SensorWithLoop.py'): 'SensorWithLoop.py',
            os.path.join(settings.REPO_DIR, 'devices', 'LedStrip.py'): 'LedStrip.py',
            os.path.join(settings.REPO_DIR, 'devices', 'DimmableLight.py'): 'DimmableLight.py',
            os.path.join(settings.REPO_DIR, 'devices', 'HttpGet.py'): 'HttpGet.py',
            os.path.join(settings.REPO_DIR, 'devices', 'IrBlaster.py'): 'IrBlaster.py',
            os.path.join(settings.REPO_DIR, 'core', 'Instance.py'): 'Instance.py',
            os.path.join(settings.REPO_DIR, 'core', 'Config.py'): 'Config.py',
            os.path.join(settings.REPO_DIR, 'core', 'Group.py'): 'Group.py',
            os.path.join(settings.REPO_DIR, 'core', 'SoftwareTimer.py'): 'SoftwareTimer.py',
            os.path.join(settings.REPO_DIR, 'core', 'app_context.py'): 'app_context.py',
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
            os.path.join(settings.REPO_DIR, 'core', 'app_context.py'): 'app_context.py',
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
            os.path.join(settings.REPO_DIR, 'devices', 'TasmotaRelay.py'): 'TasmotaRelay.py',
            os.path.join(settings.REPO_DIR, 'sensors', 'MotionSensor.py'): 'MotionSensor.py',
            os.path.join(settings.REPO_DIR, 'sensors', 'Dummy.py'): 'Dummy.py',
            os.path.join(settings.REPO_DIR, 'devices', 'Device.py'): 'Device.py',
            os.path.join(settings.REPO_DIR, 'sensors', 'Switch.py'): 'Switch.py',
            os.path.join(settings.REPO_DIR, 'sensors', 'DesktopTrigger.py'): 'DesktopTrigger.py',
            os.path.join(settings.REPO_DIR, 'devices', 'Relay.py'): 'Relay.py',
            os.path.join(settings.REPO_DIR, 'devices', 'Tplink.py'): 'Tplink.py',
            os.path.join(settings.REPO_DIR, 'devices', 'DesktopTarget.py'): 'DesktopTarget.py',
            os.path.join(settings.REPO_DIR, 'sensors', 'Thermostat.py'): 'Thermostat.py',
            os.path.join(settings.REPO_DIR, 'sensors', 'Si7021.py'): 'Si7021.py',
            os.path.join(settings.REPO_DIR, 'sensors', 'Sensor.py'): 'Sensor.py',
            os.path.join(settings.REPO_DIR, 'sensors', 'SensorWithLoop.py'): 'SensorWithLoop.py',
            os.path.join(settings.REPO_DIR, 'devices', 'LedStrip.py'): 'LedStrip.py',
            os.path.join(settings.REPO_DIR, 'devices', 'DimmableLight.py'): 'DimmableLight.py',
            os.path.join(settings.REPO_DIR, 'devices', 'HttpGet.py'): 'HttpGet.py',
            os.path.join(settings.REPO_DIR, 'core', 'Instance.py'): 'Instance.py',
            os.path.join(settings.REPO_DIR, 'core', 'Config.py'): 'Config.py',
            os.path.join(settings.REPO_DIR, 'core', 'Group.py'): 'Group.py',
            os.path.join(settings.REPO_DIR, 'core', 'SoftwareTimer.py'): 'SoftwareTimer.py',
            os.path.join(settings.REPO_DIR, 'core', 'app_context.py'): 'app_context.py',
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
            os.path.join(settings.REPO_DIR, 'devices', 'TasmotaRelay.py'): 'TasmotaRelay.py',
            os.path.join(settings.REPO_DIR, 'sensors', 'MotionSensor.py'): 'MotionSensor.py',
            os.path.join(settings.REPO_DIR, 'sensors', 'Dummy.py'): 'Dummy.py',
            os.path.join(settings.REPO_DIR, 'devices', 'Device.py'): 'Device.py',
            os.path.join(settings.REPO_DIR, 'sensors', 'Switch.py'): 'Switch.py',
            os.path.join(settings.REPO_DIR, 'sensors', 'DesktopTrigger.py'): 'DesktopTrigger.py',
            os.path.join(settings.REPO_DIR, 'devices', 'Relay.py'): 'Relay.py',
            os.path.join(settings.REPO_DIR, 'devices', 'Tplink.py'): 'Tplink.py',
            os.path.join(settings.REPO_DIR, 'devices', 'DesktopTarget.py'): 'DesktopTarget.py',
            os.path.join(settings.REPO_DIR, 'sensors', 'Sensor.py'): 'Sensor.py',
            os.path.join(settings.REPO_DIR, 'sensors', 'SensorWithLoop.py'): 'SensorWithLoop.py',
            os.path.join(settings.REPO_DIR, 'devices', 'LedStrip.py'): 'LedStrip.py',
            os.path.join(settings.REPO_DIR, 'devices', 'DimmableLight.py'): 'DimmableLight.py',
            os.path.join(settings.REPO_DIR, 'devices', 'HttpGet.py'): 'HttpGet.py',
            os.path.join(settings.REPO_DIR, 'devices', 'IrBlaster.py'): 'IrBlaster.py',
            os.path.join(settings.REPO_DIR, 'core', 'Instance.py'): 'Instance.py',
            os.path.join(settings.REPO_DIR, 'core', 'Config.py'): 'Config.py',
            os.path.join(settings.REPO_DIR, 'core', 'Group.py'): 'Group.py',
            os.path.join(settings.REPO_DIR, 'core', 'SoftwareTimer.py'): 'SoftwareTimer.py',
            os.path.join(settings.REPO_DIR, 'core', 'app_context.py'): 'app_context.py',
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
            os.path.join(settings.REPO_DIR, 'core', 'app_context.py'): 'app_context.py',
            os.path.join(settings.REPO_DIR, 'core', 'Api.py'): 'Api.py',
            os.path.join(settings.REPO_DIR, 'core', 'util.py'): 'util.py',
            os.path.join(settings.REPO_DIR, 'core', 'main.py'): 'main.py'
        }

        modules = get_modules(self.config, settings.REPO_DIR)
        self.assertEqual(modules, expected_modules)


# Test view that connects to existing node, downloads config file, writes to database
class RestoreConfigViewTest(TestCase):
    def setUp(self):
        # Set default content_type for post requests (avoid long lines)
        self.client = JSONClient()

    def test_restore_config(self):
        # Database should be empty
        self.assertEqual(len(Config.objects.all()), 0)
        self.assertEqual(len(Node.objects.all()), 0)

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

        # Config and Node should now exist
        self.assertEqual(len(Config.objects.all()), 1)
        self.assertEqual(len(Node.objects.all()), 1)
        self.assertTrue(Config.objects.get(filename='test1.json'))
        self.assertTrue(Node.objects.get(friendly_name='Test1'))

        # Config should be identical to input object
        config = Config.objects.get(filename='test1.json').config
        self.assertEqual(config, test_config_1)
        self.assertEqual(len(config['schedule_keywords']), 2)
        self.assertIn('sunrise', config['schedule_keywords'].keys())
        self.assertIn('sunset', config['schedule_keywords'].keys())

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
class ReuploadAllTests(TestCase):
    def setUp(self):
        create_test_nodes()

        self.failed_to_connect = {
            'message': 'Unable to connect to node, please make sure it is connected to wifi and try again.',
            'status': 404
        }

        # Mock ThreadPoolExecutor to run tasks serially (avoid multiple threads
        # trying to read simultaneously, django unit tests add database locks)
        self.mock_executor = patch('node_configuration.views.ThreadPoolExecutor')
        mock_executor = self.mock_executor.start()
        mock_executor.return_value.__enter__.return_value.map = map

    def tearDown(self):
        self.mock_executor.stop()

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
class ChangeNodeIpTests(TestCase):
    def setUp(self):
        # Set default content_type for post requests (avoid long lines)
        self.client = JSONClient()

        # Create 3 test nodes
        create_test_nodes()

    def test_change_node_ip(self):
        # Confirm starting IP
        self.assertEqual(Node.objects.all()[0].ip, '192.168.1.123')

        # Mock provision to return success message
        with patch('node_configuration.views.provision') as mock_provision:
            mock_provision.return_value = {'message': 'Upload complete.', 'status': 200}

            # Make request, confirm response
            request_payload = {
                'friendly_name': 'Test1',
                'new_ip': '192.168.1.255',
                'reupload': True
            }
            response = self.client.post('/change_node_ip', request_payload)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()['message'], 'Successfully uploaded to new IP')

            # Confirm node model IP changed, upload was called
            self.assertEqual(Node.objects.all()[0].ip, '192.168.1.255')
            self.assertEqual(mock_provision.call_count, 1)

    def test_change_node_ip_no_reupload(self):
        # Confirm starting IP
        self.assertEqual(Node.objects.all()[0].ip, '192.168.1.123')

        # Mock provision to confirm not called
        with patch('node_configuration.views.provision') as mock_provision:

            # Make request with reupload param set to False (changed IP from CLI)
            request_payload = {
                'friendly_name': 'Test1',
                'new_ip': '192.168.1.255',
                'reupload': False
            }

            # Confirm response, confirm node model IP changed
            response = self.client.post('/change_node_ip', request_payload)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()['message'], 'Successfully changed IP')
            self.assertEqual(Node.objects.all()[0].ip, '192.168.1.255')

            # Confirm provision was NOT called
            mock_provision.assert_not_called()

    def test_target_ip_offline(self):
        # Mock provision to return failure message without doing anything
        with patch('node_configuration.views.provision') as mock_provision:
            mock_provision.return_value = {
                'message': 'Unable to connect to node, please make sure it is connected to wifi and try again.',
                'status': 404
            }

            # Make request, confirm error
            request_payload = {
                'friendly_name': 'Test1',
                'new_ip': '192.168.1.255',
                'reupload': True
            }
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
        request_payload = {
            'friendly_name': 'Test1',
            'new_ip': '192.168.1.555',
            'reupload': True
        }
        response = self.client.post('/change_node_ip', request_payload)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['message'], 'Invalid IP 192.168.1.555')

        # Make request targeting non-existing node, confirm error
        request_payload = {
            'friendly_name': 'Test9',
            'new_ip': '192.168.1.255',
            'reupload': True
        }
        response = self.client.post('/change_node_ip', request_payload)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()['message'], "Unable to change IP, node does not exist")

        # Make request with current IP, confirm error
        request_payload = {
            'friendly_name': 'Test1',
            'new_ip': '192.168.1.123',
            'reupload': True
        }
        response = self.client.post('/change_node_ip', request_payload)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['message'], 'New IP must be different than old')
