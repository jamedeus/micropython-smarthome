import os
import json
import types
from unittest.mock import patch, MagicMock
from django.conf import settings
from django.core.exceptions import ValidationError
from .models import Config, Node, ScheduleKeyword, GpsCoordinates

# Functions used to manage cli_config.json
from helper_functions import get_cli_config, remove_node_from_cli_config

# Large JSON objects, helper functions
from .unit_test_helpers import (
    TestCaseBackupRestore,
    JSONClient,
    test_config_1,
    test_config_2,
    create_config_and_node_from_json
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


# Test the Node model
class NodeTests(TestCaseBackupRestore):
    def test_create_node(self):
        self.assertEqual(len(Node.objects.all()), 0)

        # Create node, confirm exists in database
        node = Node.objects.create(friendly_name='Unit Test Node', ip='123.45.67.89', floor='2')
        self.assertEqual(len(Node.objects.all()), 1)
        self.assertIsInstance(node, Node)

        # Confirm friendly name shown when instance printed
        self.assertEqual(node.__str__(), 'Unit Test Node')

        # Confirm attributes, should not have config reverse relation
        self.assertEqual(node.friendly_name, 'Unit Test Node')
        self.assertEqual(node.ip, '123.45.67.89')
        self.assertEqual(node.floor, 2)
        with self.assertRaises(Node.config.RelatedObjectDoesNotExist):
            print(node.config)

        # Create Config with reverse relation, confirm accessible both ways
        config = Config.objects.create(config=test_config_1, filename='test1.json', node=node)
        self.assertEqual(node.config, config)
        self.assertEqual(config.node, node)

    def test_create_node_invalid(self):
        # Confirm starting condition
        self.assertEqual(len(Node.objects.all()), 0)

        # Should refuse to create with no arguments, only floor has default
        with self.assertRaises(ValidationError):
            Node.objects.create()

        # Should refuse to create with invalid IP
        with self.assertRaises(ValidationError):
            Node.objects.create(friendly_name='Unit Test Node', ip='123.456.789.10')

        # Should refuse to create negative floor below -999
        with self.assertRaises(ValidationError):
            Node.objects.create(friendly_name='Unit Test Node', ip='123.45.67.89', floor='-1000')

        # Should refuse to create floor over 999
        with self.assertRaises(ValidationError):
            Node.objects.create(friendly_name='Unit Test Node', ip='123.45.67.89', floor='1000')

        # Should refuse to create non-int floor
        with self.assertRaises(ValidationError):
            Node.objects.create(friendly_name='Unit Test Node', ip='123.45.67.89', floor='upstairs')

        # Should refuse to create with friendly name >50 characters
        with self.assertRaises(ValidationError):
            Config.objects.create(
                config=test_config_1,
                filename='Unrealistically Long Friendly Name That Nobody Needs'
            )

        # Confirm no nodes were created
        self.assertEqual(len(Node.objects.all()), 0)

    def test_create_duplicate_node(self):
        # Create node, confirm number in database
        Node.objects.create(friendly_name='Unit Test Node', ip='123.45.67.89', floor='2')
        self.assertEqual(len(Node.objects.all()), 1)

        # Should refuse to create another node with same name
        with self.assertRaises(ValidationError):
            Node.objects.create(friendly_name='Unit Test Node', ip='123.45.1.9', floor='3')

        # Confirm no nodes created in db
        self.assertEqual(len(Node.objects.all()), 1)

    def test_cli_sync(self):
        # Path to config file that will be created
        config_path = os.path.join(settings.CONFIG_DIR, 'test1.json')

        # Confirm node not in cli_config.json, config not on disk
        remove_node_from_cli_config('Unit Test Node')
        self.assertFalse(os.path.exists(config_path))

        # Create node, should not be added to cli_config.json (node has no config file)
        node = Node.objects.create(friendly_name='Unit Test Node', ip='123.45.67.89', floor='2')
        cli_config = get_cli_config()
        self.assertNotIn('unit-test-node', cli_config['nodes'].keys())
        self.assertFalse(os.path.exists(config_path))

        # Create Config with reverse relation, node should be added to cli_config.json
        Config.objects.create(config=test_config_1, filename='test1.json', node=node)
        cli_config = get_cli_config()
        self.assertIn('unit-test-node', cli_config['nodes'].keys())
        self.assertEqual(cli_config['nodes']['unit-test-node'], '123.45.67.89')

        # Delete node, should removed node from cli_config.json, should remove config from disk
        node.delete()
        cli_config = get_cli_config()
        self.assertNotIn('unit-test-node', cli_config['nodes'].keys())
        self.assertFalse(os.path.exists(config_path))

    # Original issue: Node model validator raised ValidationError if floor was
    # negative, but config validator and edit_config page only require floor to
    # be between -999 and 999. If the user created a config with negative floor
    # and uploaded a 500 error was returned and the Node model was not created.
    def test_regression_create_node_with_negative_floor(self):
        self.assertEqual(len(Node.objects.all()), 0)

        # Create node with negative floor, confirm exists in database
        node = Node.objects.create(friendly_name='Basement', ip='123.45.67.89', floor='-1')
        self.assertEqual(len(Node.objects.all()), 1)
        self.assertIsInstance(node, Node)


# Test the Config model
class ConfigTests(TestCaseBackupRestore):
    def test_create_config(self):
        # Confirm starting condition
        self.assertEqual(len(Config.objects.all()), 0)

        # Create node, confirm exists in database, file exists on disk
        config = Config.objects.create(config=test_config_1, filename='test1.json')
        self.assertEqual(len(Config.objects.all()), 1)
        self.assertIsInstance(config, Config)
        self.assertTrue(os.path.exists(os.path.join(settings.CONFIG_DIR, 'test1.json')))

        # Confirm filename shown when instance printed
        self.assertEqual(config.__str__(), 'test1.json')

        # Confirm attributes, confirm no node reverse relation
        self.assertEqual(config.config, test_config_1)
        self.assertEqual(config.filename, 'test1.json')
        self.assertIsNone(config.node)

        # Create Node, add reverse relation
        node = Node.objects.create(friendly_name='Unit Test Node', ip='123.45.67.89', floor='2')
        config.node = node
        config.save()

        # Confirm accessible both ways
        self.assertEqual(config.node, node)
        self.assertEqual(node.config, config)

    def test_create_config_invalid(self):
        # Confirm starting condition
        self.assertEqual(len(Config.objects.all()), 0)

        # Should refuse to create with no arguments
        with self.assertRaises(ValidationError):
            Config.objects.create()

        # Should refuse to create with filename >50 characters
        with self.assertRaises(ValidationError):
            Config.objects.create(
                config=test_config_1,
                filename='unrealistically-long-config-name-that-nobody-needs.json'
            )

        # Confirm no configs created in db
        self.assertEqual(len(Config.objects.all()), 0)

    def test_duplicate_filename(self):
        # Create config, confirm number in database
        Config.objects.create(config=test_config_1, filename='test1.json')
        self.assertEqual(len(Config.objects.all()), 1)

        # Should refuse to create another config with same name
        with self.assertRaises(ValidationError):
            Config.objects.create(config=test_config_1, filename='test1.json')

        # Confirm no configs created in db
        self.assertEqual(len(Config.objects.all()), 1)

    def test_write_to_disk(self):
        # Create config
        config = Config.objects.create(config=test_config_1, filename='write_to_disk.json')

        # Delete from disk, confirm removed
        os.remove(os.path.join(settings.CONFIG_DIR, 'write_to_disk.json'))
        self.assertFalse(os.path.exists(os.path.join(settings.CONFIG_DIR, 'write_to_disk.json')))

        # Call method, should exist
        config.write_to_disk()
        self.assertTrue(os.path.exists(os.path.join(settings.CONFIG_DIR, 'write_to_disk.json')))

        # Contents should match config attribute
        with open(os.path.join(settings.CONFIG_DIR, 'write_to_disk.json'), 'r') as file:
            output = json.load(file)
            self.assertEqual(config.config, output)

        # Remove file, prevent test failing after first run
        os.remove(os.path.join(settings.CONFIG_DIR, 'write_to_disk.json'))

    def test_read_from_disk(self):
        # Create config
        config = Config.objects.create(config=test_config_1, filename='read_from_disk.json')

        # Write different config to expected config path
        with open(os.path.join(settings.CONFIG_DIR, 'read_from_disk.json'), 'w') as file:
            json.dump(test_config_2, file)

        # Confirm configs are different
        self.assertNotEqual(config.config, test_config_2)

        # Call method, configs should now be identical
        config.read_from_disk()
        self.assertEqual(config.config, test_config_2)

        # Remove file
        os.remove(os.path.join(settings.CONFIG_DIR, 'read_from_disk.json'))

    def test_cli_sync(self):
        # Path to config file that will be created, confirm does not exist
        config_path = os.path.join(settings.CONFIG_DIR, 'test1.json')
        self.assertFalse(os.path.exists(config_path))

        # Create Config, should write config file to disk automatically
        config = Config.objects.create(config=test_config_1, filename='test1.json')
        self.assertTrue(os.path.exists(config_path))

        # Delete from disk, call save method, should be written again
        os.remove(config_path)
        config.save()
        self.assertTrue(os.path.exists(config_path))

        # Delete model, file should be removed from disk automatically
        config.delete()
        self.assertFalse(os.path.exists(config_path))

    def test_cli_sync_disabled(self):
        # Set CLI_SYNC to False
        settings.CLI_SYNC = False

        # Path to config file that would be created with CLI_SYNC, confirm does not exist
        config_path = os.path.join(settings.CONFIG_DIR, 'test1.json')
        self.assertFalse(os.path.exists(config_path))

        # Create Config, config should NOT be written to disk
        config = Config.objects.create(config=test_config_1, filename='test1.json')
        self.assertFalse(os.path.exists(config_path))

        # Call write_to_disk, confirm correctly ignored
        config.write_to_disk()
        self.assertFalse(os.path.exists(config_path))

        # Write empty dict to expected config path
        with open(config_path, 'w') as file:
            json.dump({}, file)

        # Call read_from_disk, confirm correctly ignored, config not effected
        config.read_from_disk()
        self.assertEqual(config.config, test_config_1)

        # Revert
        settings.CLI_SYNC = True
        os.remove(config_path)


class GpsCoordinatesTests(TestCaseBackupRestore):
    def setUp(self):
        # Set default content_type for post requests (avoid long lines)
        self.client = JSONClient()

        # Create config with no coordinates set
        self.config = Config.objects.create(config=test_config_1, filename='test1.json')

    def test_get_location_suggestions(self):
        with patch('requests.get') as mock_get:
            # Mock requests.get to return arbitrary response
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = [{"place_id": 12345}, {"place_id": 67890}]
            mock_get.return_value = mock_response

            # Request location suggestions, confirm correct response
            response = self.client.get('/get_location_suggestions/somewhere')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json(), {
                'status': 'success',
                'message': [{"place_id": 12345}, {"place_id": 67890}]
            })

    def test_get_location_suggestions_error(self):
        with patch('requests.get') as mock_get:
            # Mock requests.get to return missing API key error
            mock_response = MagicMock()
            mock_response.status_code = 401
            mock_response.text = 'HTTP 401: Missing API Key\r\n\r\nYour request is missing an api_key'
            mock_get.return_value = mock_response

            # Request location suggestions, confirm correct error
            response = self.client.get('/get_location_suggestions/somewhere')
            self.assertEqual(response.status_code, 401)
            self.assertEqual(response.json(), {
                'status': 'error',
                'message': 'HTTP 401: Missing API Key\r\n\r\nYour request is missing an api_key'
            })

    def test_setting_coordinates(self):
        # Database should be empty, config metadata should not contain gps key
        self.assertEqual(len(GpsCoordinates.objects.all()), 0)
        self.assertNotIn('gps', self.config.config['metadata'].keys())

        # Set default credentials, verify response + database
        response = self.client.post(
            '/set_default_location',
            {'name': 'Portland', 'lat': '45.689122409097', 'lon': '-122.63675124859863'}
        )
        self.assertEqual(response.json()['message'], 'Location set')
        self.assertEqual(len(GpsCoordinates.objects.all()), 1)

        # Overwrite credentials, verify model only contains 1 entry
        response = self.client.post(
            '/set_default_location',
            {'name': 'Dallas', 'lat': '32.99171902655', 'lon': '-96.77213361367663'}
        )
        self.assertEqual(response.json()['message'], 'Location set')
        self.assertEqual(len(GpsCoordinates.objects.all()), 1)

        # Confirm existing configs were updated
        self.config.refresh_from_db()
        self.assertIn('gps', self.config.config['metadata'].keys())
        self.assertEqual(self.config.config['metadata']['gps']['lat'], '32.99171902655')
        self.assertEqual(self.config.config['metadata']['gps']['lon'], '-96.77213361367663')

    def test_print_method(self):
        gps = GpsCoordinates.objects.create(
            display='Portland',
            lat='45.689122409097',
            lon='-122.63675124859863'
        )
        self.assertEqual(gps.__str__(), 'Portland')


# Test views used to manage schedule keywords from config overview
class ScheduleKeywordTests(TestCaseBackupRestore):
    def setUp(self):
        # Set default content_type for post requests (avoid long lines)
        self.client = JSONClient()

        # Create existing keyword
        self.keyword = ScheduleKeyword.objects.create(keyword='first', timestamp='00:00')

        # Config template, new keywords should be added/removed in tests
        test_config = {
            'metadata': {
                'id': 'Test1',
                'floor': '2',
                'schedule_keywords': {
                    "sunrise": "06:00",
                    "sunset": "18:00",
                    "first": "00:00"
                }
            }
        }

        # Create nodes to upload keyword to
        self.config1, self.node1 = create_config_and_node_from_json(test_config, '123.45.67.89')
        test_config['metadata']['id'] = 'Test2'
        self.config2, self.node2 = create_config_and_node_from_json(test_config, '123.45.67.98')

        # Create mock objects to replace keyword api endpoints
        self.mock_add = MagicMock()
        self.mock_add.return_value = {"Keyword added": "morning", "time": "08:00"}
        self.mock_remove = MagicMock()
        self.mock_remove.return_value = {"Keyword added": "morning", "time": "08:00"}
        self.mock_save = MagicMock()
        self.mock_save.return_value = {"Success": "Keywords written to disk"}

    def test_str_method(self):
        # Should print keyword
        self.assertEqual(self.keyword.__str__(), 'first')

    def test_add_schedule_keyword(self):
        # Confirm starting conditions
        self.assertEqual(len(ScheduleKeyword.objects.all()), 3)
        self.assertEqual(
            self.node1.config.config['metadata']['schedule_keywords'],
            {'sunrise': '06:00', 'sunset': '18:00', 'first': '00:00'}
        )
        self.assertEqual(
            self.config2.config['metadata']['schedule_keywords'],
            {'sunrise': '06:00', 'sunset': '18:00', 'first': '00:00'}
        )

        # Mock all keyword endpoints, prevent failed network requests
        with patch('node_configuration.views.add_schedule_keyword', side_effect=self.mock_add), \
             patch('node_configuration.views.remove_schedule_keyword', side_effect=self.mock_remove), \
             patch('node_configuration.views.save_schedule_keywords', side_effect=self.mock_save):

            # Send request, confirm response, confirm model created
            data = {'keyword': 'morning', 'timestamp': '08:00'}
            response = self.client.post('/add_schedule_keyword', data)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()['message'], 'Keyword created')
            self.assertEqual(len(ScheduleKeyword.objects.all()), 4)

            # Should call add and save once for each node
            self.assertEqual(self.mock_add.call_count, 2)
            self.assertEqual(self.mock_remove.call_count, 0)
            self.assertEqual(self.mock_save.call_count, 2)

        # All configs should contain new keyword
        self.node1.refresh_from_db()
        self.config2.refresh_from_db()
        self.assertEqual(
            self.node1.config.config['metadata']['schedule_keywords']['morning'],
            '08:00'
        )
        self.assertEqual(
            self.config2.config['metadata']['schedule_keywords']['morning'],
            '08:00'
        )

    def test_edit_schedule_keyword_timestamp(self):
        self.assertEqual(len(ScheduleKeyword.objects.all()), 3)
        self.assertEqual(
            self.node1.config.config['metadata']['schedule_keywords'],
            {'sunrise': '06:00', 'sunset': '18:00', 'first': '00:00'}
        )
        self.assertEqual(
            self.config2.config['metadata']['schedule_keywords'],
            {'sunrise': '06:00', 'sunset': '18:00', 'first': '00:00'}
        )

        # Mock all keyword endpoints, prevent failed network requests
        with patch('node_configuration.views.add_schedule_keyword', side_effect=self.mock_add), \
             patch('node_configuration.views.remove_schedule_keyword', side_effect=self.mock_remove), \
             patch('node_configuration.views.save_schedule_keywords', side_effect=self.mock_save):

            # Send request to change timestamp only, should overwrite existing keyword
            data = {'keyword_old': 'first', 'keyword_new': 'first', 'timestamp_new': '01:00'}
            response = self.client.post('/edit_schedule_keyword', data)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()['message'], 'Keyword updated')

            # Should call add and save once for each node, should not call remove
            self.assertEqual(self.mock_add.call_count, 2)
            self.assertEqual(self.mock_remove.call_count, 0)
            self.assertEqual(self.mock_save.call_count, 2)

            # Confirm no model entry created, existing has new timestamp same keyword
            self.assertEqual(len(ScheduleKeyword.objects.all()), 3)
            self.keyword.refresh_from_db()
            self.assertEqual(self.keyword.keyword, 'first')
            self.assertEqual(self.keyword.timestamp, '01:00')

        # All configs should contain new keyword
        self.node1.refresh_from_db()
        self.config2.refresh_from_db()
        self.assertEqual(
            self.node1.config.config['metadata']['schedule_keywords']['first'],
            '01:00'
        )
        self.assertEqual(
            self.config2.config['metadata']['schedule_keywords']['first'],
            '01:00'
        )

    def test_edit_schedule_keyword_keyword(self):
        self.assertEqual(len(ScheduleKeyword.objects.all()), 3)

        # Mock all keyword endpoints, prevent failed network requests
        with patch('node_configuration.views.add_schedule_keyword', side_effect=self.mock_add), \
             patch('node_configuration.views.remove_schedule_keyword', side_effect=self.mock_remove), \
             patch('node_configuration.views.save_schedule_keywords', side_effect=self.mock_save):

            # Send request to change keyword, should remove and replace existing keyword
            data = {'keyword_old': 'first', 'keyword_new': 'second', 'timestamp_new': '08:00'}
            response = self.client.post('/edit_schedule_keyword', data)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()['message'], 'Keyword updated')

            # Should call add, remove, and save once for each node
            self.assertEqual(self.mock_add.call_count, 2)
            self.assertEqual(self.mock_remove.call_count, 2)
            self.assertEqual(self.mock_save.call_count, 2)

            # Confirm same number of model entries, existing has new timestamp same keyword
            self.assertEqual(len(ScheduleKeyword.objects.all()), 3)
            self.keyword.refresh_from_db()
            self.assertEqual(self.keyword.keyword, 'second')
            self.assertEqual(self.keyword.timestamp, '08:00')

        # Keyword should update on all existing configs
        self.node1.refresh_from_db()
        self.config2.refresh_from_db()
        self.assertNotIn('first', self.node1.config.config['metadata']['schedule_keywords'].keys())
        self.assertNotIn('first', self.config2.config['metadata']['schedule_keywords'].keys())
        self.assertEqual(
            self.node1.config.config['metadata']['schedule_keywords']['second'],
            '08:00'
        )
        self.assertEqual(
            self.config2.config['metadata']['schedule_keywords']['second'],
            '08:00'
        )

    def test_delete_schedule_keyword(self):
        # Confirm starting condition
        self.assertEqual(len(ScheduleKeyword.objects.all()), 3)

        # Mock all keyword endpoints, prevent failed network requests
        with patch('node_configuration.views.add_schedule_keyword', side_effect=self.mock_add), \
             patch('node_configuration.views.remove_schedule_keyword', side_effect=self.mock_remove), \
             patch('node_configuration.views.save_schedule_keywords', side_effect=self.mock_save):

            # Send request to delete keyword, verify response
            response = self.client.post('/delete_schedule_keyword', {'keyword': 'first'})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()['message'], 'Keyword deleted')

            # Should call remove and save once for each node, should not call add
            self.assertEqual(self.mock_add.call_count, 0)
            self.assertEqual(self.mock_remove.call_count, 2)
            self.assertEqual(self.mock_save.call_count, 2)

            # Confirm model deleted
            self.assertEqual(len(ScheduleKeyword.objects.all()), 2)

        # Should be removed from all existing configs
        self.node1.refresh_from_db()
        self.config2.refresh_from_db()
        self.assertNotIn('first', self.node1.config.config['metadata']['schedule_keywords'].keys())
        self.assertNotIn('first', self.config2.config['metadata']['schedule_keywords'].keys())

    # Original issue: Views directly imported 3 endpoint functions from api_endpoints.
    # Decorators adding wrapper functions were later added to api_endpoints to reduce
    # code repetition. This removed the original reference from module namespace,
    # leading views to import NoneType objects instead of functions. Attempting to call
    # NoneType objects in ThreadPoolExecutor resulted in an immediate return, without
    # calling any endpoints. All unit tests above continued to pass because they mock
    # the endpoints in question.
    # Fixed by importing decorated functions from endpoint_map object
    def test_regression_endpoints_imported_as_nonetype(self):
        from node_configuration import views
        self.assertIsNotNone(views.add_schedule_keyword)
        self.assertIsNotNone(views.remove_schedule_keyword)
        self.assertIsNotNone(views.save_schedule_keywords)
        self.assertEqual(type(views.add_schedule_keyword), types.FunctionType)
        self.assertEqual(type(views.remove_schedule_keyword), types.FunctionType)
        self.assertEqual(type(views.save_schedule_keywords), types.FunctionType)


# Confirm schedule keyword management endpoints raise correct errors
class ScheduleKeywordErrorTests(TestCaseBackupRestore):
    def setUp(self):
        # Set default content_type for post requests (avoid long lines)
        self.client = JSONClient()

        # Create existing keyword
        self.keyword = ScheduleKeyword.objects.create(keyword='first', timestamp='00:00')

    def test_add_invalid_timestamp(self):
        # Send request, confirm error, confirm no model created
        self.assertEqual(len(ScheduleKeyword.objects.all()), 3)
        data = {'keyword': 'morning', 'timestamp': '8:00'}
        response = self.client.post('/add_schedule_keyword', data)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json()['message'],
            "{'timestamp': ['Timestamp format must be HH:MM (no AM/PM).']}"
        )
        self.assertEqual(len(ScheduleKeyword.objects.all()), 3)

    def test_add_duplicate_keyword(self):
        # Send request, confirm error, confirm no model created
        self.assertEqual(len(ScheduleKeyword.objects.all()), 3)
        data = {'keyword': 'sunrise', 'timestamp': '08:00'}
        response = self.client.post('/add_schedule_keyword', data)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json()['message'],
            "{'keyword': ['Schedule keyword with this Keyword already exists.']}"
        )
        self.assertEqual(len(ScheduleKeyword.objects.all()), 3)

    def test_edit_invalid_timestamp(self):
        # Send request, confirm error
        data = {'keyword_old': 'first', 'keyword_new': 'second', 'timestamp_new': '8:00'}
        response = self.client.post('/edit_schedule_keyword', data)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json()['message'],
            "{'timestamp': ['Timestamp format must be HH:MM (no AM/PM).']}"
        )

    def test_edit_duplicate_keyword(self):
        # Send request, confirm error
        data = {'keyword_old': 'first', 'keyword_new': 'sunrise', 'timestamp_new': '08:00'}
        response = self.client.post('/edit_schedule_keyword', data)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json()['message'],
            "{'keyword': ['Schedule keyword with this Keyword already exists.']}"
        )

    def test_edit_non_existing_keyword(self):
        # Send request to edit keyword, verify error
        data = {'keyword_old': 'fake', 'keyword_new': 'second', 'timestamp_new': '8:00'}
        response = self.client.post('/edit_schedule_keyword', data)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()['message'], 'Keyword not found')

    def test_delete_non_existing_keyword(self):
        # Send request to delete keyword, verify error
        response = self.client.post('/delete_schedule_keyword', {'keyword': 'fake'})
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()['message'], 'Keyword not found')

    # Should not be able to delete sunrise or sunset
    def test_delete_required_keyword(self):
        # Send request to delete keyword, verify error
        response = self.client.post('/delete_schedule_keyword', {'keyword': 'sunrise'})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['message'], "sunrise is required and cannot be deleted")

        response = self.client.post('/delete_schedule_keyword', {'keyword': 'sunset'})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['message'], "sunset is required and cannot be deleted")

    def test_invalid_get_request(self):
        # All keyword endpoints require post, confirm errors
        response = self.client.get('/add_schedule_keyword')
        self.assertEqual(response.status_code, 405)
        self.assertEqual(response.json()['message'], 'Must post data')

        response = self.client.get('/edit_schedule_keyword')
        self.assertEqual(response.status_code, 405)
        self.assertEqual(response.json()['message'], 'Must post data')

        response = self.client.get('/delete_schedule_keyword')
        self.assertEqual(response.status_code, 405)
        self.assertEqual(response.json()['message'], 'Must post data')
