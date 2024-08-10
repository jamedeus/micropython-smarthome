import os
import json
import tempfile
from copy import deepcopy
from unittest import TestCase
from unittest.mock import patch, MagicMock, mock_open
from cli_config_manager import CliConfigManager
from mock_cli_config import mock_cli_config, mock_cli_config_path, mock_config_dir


class TestCliConfigManager(TestCase):
    def setUp(self):
        # Mock path to cli_config.json (prevent overwriting real file)
        self.cli_config_patch = patch(
            'cli_config_manager.cli_config_path',
            mock_cli_config_path
        )
        self.cli_config_patch.start()

        # Instantiate manager
        self.manager = CliConfigManager()

    def tearDown(self):
        self.cli_config_patch.stop()

        # Reset manager config to original contents (isolate tests)
        self.manager.config = deepcopy(mock_cli_config)

        # Overwrite mock_cli_config with original contents
        with open(mock_cli_config_path, 'w', encoding='utf-8') as file:
            json.dump(mock_cli_config, file)

        # Delete test configs created in tests
        if os.path.exists(os.path.join(mock_config_dir, 'new.json')):
            os.remove(os.path.join(mock_config_dir, 'new.json'))

    def test_read_cli_config_from_disk(self):
        # Confirm returns contents of cli_config.json
        self.assertEqual(
            self.manager.read_cli_config_from_disk(),
            mock_cli_config
        )

    def test_read_cli_config_from_disk_missing_file(self):
        # Simulate missing cli_config.json, mock config dir path
        with patch('builtins.open', side_effect=FileNotFoundError), \
             patch('os.path.join', return_value=mock_config_dir):

            # Confirm returns cli_config.json template
            self.assertEqual(
                self.manager.read_cli_config_from_disk(),
                {
                    'nodes': {},
                    'schedule_keywords': {},
                    'webrepl_password': 'password',
                    'config_directory': mock_config_dir
                }
            )

    def test_sync_from_django(self):
        # Create mock response object
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'status': 'success',
            'message': {
                'nodes': mock_cli_config['nodes'],
                'schedule_keywords': mock_cli_config['schedule_keywords']
            }
        }

        # Mock _client.get to return mock response object
        with patch.object(self.manager, '_client', MagicMock()) as mock_client, \
             patch.object(mock_client, 'get', return_value=mock_response) as mock_get, \
             patch.object(self.manager, 'write_cli_config_to_disk') as mock_write_to_disk:

            # Call sync method
            self.manager.sync_from_django()

            # Confirm _client.get was called with correct URL
            mock_get.assert_called_once_with(
                f'{mock_cli_config["django_backend"]}/get_cli_config',
                timeout=5
            )

            # Confirm write_cli_config_to_disk was called
            mock_write_to_disk.assert_called_once()

    def test_sync_from_django_no_backend_configured(self):
        with self.assertRaises(RuntimeError):
            # Mock CliConfigManager.config to an empty dict (no django_backend key)
            # Mock _client.get to confirm no request is made
            with patch.object(self.manager, 'config', {}), \
                 patch.object(self.manager, '_client', MagicMock()) as mock_client, \
                 patch.object(mock_client, 'get') as mock_get:

                # Call sync method, confirm no request was made
                self.manager.sync_from_django()
                mock_get.assert_not_called()

    def test_sync_from_django_failed_connection_(self):
        # Mock _client.get to simulate connection error
        with patch.object(self.manager, '_client', MagicMock()) as mock_client, \
             patch.object(mock_client, 'get', side_effect=OSError) as mock_get, \
             patch.object(self.manager, 'write_cli_config_to_disk') as mock_write_to_disk:

            # Call sync method, confirm write_cli_config_to_disk was NOT called
            self.manager.sync_from_django()
            mock_write_to_disk.assert_not_called()

        # Create mock response object with bad status code
        mock_response = MagicMock()
        mock_response.status_code = 404

        # Mock _client.get to return mock response object
        with patch.object(self.manager, '_client', MagicMock()) as mock_client, \
             patch.object(mock_client, 'get', return_value=mock_response) as mock_get, \
             patch.object(self.manager, 'write_cli_config_to_disk') as mock_write_to_disk:

            # Call sync method, confirm write_cli_config_to_disk was NOT called
            self.manager.sync_from_django()
            mock_write_to_disk.assert_not_called()

    def test_get_existing_node_names(self):
        self.assertEqual(
            self.manager.get_existing_node_names(),
            ['node1', 'node2', 'node3']
        )

    def test_add_node(self):
        # Create mock response object
        mock_response = MagicMock()
        mock_response.status_code = 200

        # Confirm config object does not contain name that will be added
        self.assertNotIn('new-node', self.manager.config['nodes'])

        # Mock _client.post to return mock response object
        # Mock load_node_config_file to return empty dict (mock config json)
        # Mock _csrf_token to predictable value
        with patch.object(self.manager, '_client', MagicMock()) as mock_client, \
             patch.object(mock_client, 'post', return_value=mock_response) as mock_post, \
             patch.object(self.manager, 'load_node_config_file', return_value={}), \
             patch.object(self.manager, '_csrf_token', None):

            # Call add_node method
            self.manager.add_node('New Node', '192.168.1.63')

            # Confirm node was added to manager config attribute and file on disk
            self.assertIn('new-node', self.manager.config['nodes'])
            with open(mock_cli_config_path, 'r') as file:
                config = json.load(file)
            self.assertIn('new-node', config['nodes'])

            # Confirm new node was posted to django backend
            mock_post.assert_called_once_with(
                f'{self.manager.config["django_backend"]}/add_node',
                json={
                    'ip': '192.168.1.63',
                    'config': {}
                },
                headers={
                    'X-CSRFToken': None
                },
                timeout=5
            )

    def test_add_node_no_backend_configured(self):
        # Confirm config object does not contain name that will be added
        self.assertNotIn('new-node', self.manager.config['nodes'])

        # Create mock cli_config.json with no django backend configured
        mock_cli_config_no_backend = deepcopy(mock_cli_config)
        del mock_cli_config_no_backend['django_backend']

        # Mock CliConfigManager.config remove django_backend key
        # Mock _client.post to confirm no request is made
        with patch.object(self.manager, 'config', mock_cli_config_no_backend), \
             patch.object(self.manager, '_client', MagicMock()) as mock_client, \
             patch.object(mock_client, 'post') as mock_post:

            # Call add_node method
            self.manager.add_node('New Node', '192.168.1.63')

            # Confirm node was added to manager config attribute and file on disk
            self.assertIn('new-node', self.manager.config['nodes'])
            with open(mock_cli_config_path, 'r') as file:
                config = json.load(file)
            self.assertIn('new-node', config['nodes'])

            # Confirm no POST request was made
            mock_post.assert_not_called()

    def test_remove_node(self):
        # Create mock response object
        mock_response = MagicMock()
        mock_response.status_code = 200

        # Confirm config object contains node3
        self.assertIn('node3', self.manager.config['nodes'])

        # Mock _client.post to return mock response object
        # Mock _csrf_token to predictable value
        with patch.object(self.manager, '_client', MagicMock()) as mock_client, \
             patch.object(mock_client, 'post', return_value=mock_response) as mock_post, \
             patch.object(self.manager, '_csrf_token', None):

            # Call remove_node method with name of existing node
            self.manager.remove_node('node3')

            # Confirm node3 was removed from manager config attribute and file on disk
            self.assertNotIn('node3', self.manager.config['nodes'])
            with open(mock_cli_config_path, 'r') as file:
                config = json.load(file)
            self.assertNotIn('node3', config['nodes'])

            # Confirm delete_node payload was posted to django backend
            mock_post.assert_called_once_with(
                f'{self.manager.config["django_backend"]}/delete_node',
                json='Node3',
                headers={
                    'X-CSRFToken': None
                },
                timeout=5
            )

    def test_remove_node_no_backend_configured(self):
        # Confirm config object contains node3
        self.assertIn('node3', self.manager.config['nodes'])

        # Create mock cli_config.json with no django backend configured
        mock_cli_config_no_backend = deepcopy(mock_cli_config)
        del mock_cli_config_no_backend['django_backend']

        # Mock CliConfigManager.config remove django_backend key
        # Mock _client.post to confirm no request is made
        with patch.object(self.manager, 'config', mock_cli_config_no_backend), \
             patch.object(self.manager, '_client', MagicMock()) as mock_client, \
             patch.object(mock_client, 'post') as mock_post:

            # Call remove_node method with name of existing node
            self.manager.remove_node('node3')

            # Confirm node3 was removed from manager config attribute and file on disk
            self.assertNotIn('node3', self.manager.config['nodes'])
            with open(mock_cli_config_path, 'r') as file:
                config = json.load(file)
            self.assertNotIn('node3', config['nodes'])

            # Confirm no POST request was made
            mock_post.assert_not_called()

    def test_remove_node_does_not_exist(self):
        # Confirm config object does not contain fake node
        self.assertNotIn('fake-node', self.manager.config['nodes'])

        # Mock _client.post to confirm not called
        with patch.object(self.manager, '_client', MagicMock()) as mock_client, \
             patch.object(mock_client, 'post') as mock_post:

            # Call remove_node method with fake name
            self.manager.remove_node('fake-node')

            # Confirm post was NOT called
            mock_post.assert_not_called()

    def test_remove_node_file_not_found(self):
        # Confirm config object contains node3
        self.assertIn('node3', self.manager.config['nodes'])

        # Mock _client.post to confirm not called
        # Mock os.path.exists to return False (config missing from disk)
        with patch.object(self.manager, '_client', MagicMock()) as mock_client, \
             patch.object(mock_client, 'post') as mock_post, \
             patch('os.path.exists', return_value=False):

            # Call remove_node method with name of existing node
            self.manager.remove_node('node3')

            # Confirm node3 was removed from manager config attribute and file on disk
            self.assertNotIn('node3', self.manager.config['nodes'])
            with open(mock_cli_config_path, 'r') as file:
                config = json.load(file)
            self.assertNotIn('node3', config['nodes'])

            # Confirm mock post was NOT called (couldn't get friendly name due
            # to missing config file on disk)
            mock_post.assert_not_called()

    def test_remove_node_missing_from_backend(self):
        # Create mock response object simulating node missing from backend
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.text = 'Failed to delete Node3, does not exist'

        # Confirm config object contains node3
        self.assertIn('node3', self.manager.config['nodes'])

        # Mock _client.post to return mock response object
        # Mock _csrf_token to predictable value
        with patch.object(self.manager, '_client', MagicMock()) as mock_client, \
             patch.object(mock_client, 'post', return_value=mock_response) as mock_post, \
             patch.object(self.manager, '_csrf_token', None), \
             patch('builtins.print') as mock_print:

            # Call remove_node method with name of existing node
            self.manager.remove_node('node3')

            # Confirm node3 was removed from manager config attribute and file on disk
            self.assertNotIn('node3', self.manager.config['nodes'])
            with open(mock_cli_config_path, 'r') as file:
                config = json.load(file)
            self.assertNotIn('node3', config['nodes'])

            # Confirm printed backend error response to console
            mock_print.assert_called_with('Failed to delete Node3, does not exist')

    def test_load_config_file(self):
        # Call method with mock node name, confirm returns mock config file
        # created by mock_cli_config.json
        self.assertEqual(
            self.manager.load_node_config_file('Node1'),
            {'metadata': {'id': 'Node1'}}
        )

    def test_load_config_file_does_not_exist(self):
        with self.assertRaises(FileNotFoundError):
            self.manager.load_node_config_file('Fake node')

    def test_save_node_config_file(self):
        # Confirm config file with expected name does not exist
        self.assertFalse(os.path.exists(
            os.path.join(mock_config_dir, 'new.json')
        ))

        # Call method with mock config dict
        self.manager.save_node_config_file({'metadata': {'id': 'new'}})

        # Confirm config file now exists
        self.assertTrue(os.path.exists(
            os.path.join(mock_config_dir, 'new.json')
        ))

    def test_save_node_config_file_missing_name(self):
        with self.assertRaises(ValueError):
            self.manager.save_node_config_file({})

    def test_download_node_config_file_from_django(self):
        # Create mock response object
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'status': 'success',
            'message': 'mock_config_file'
        }

        # Mock _client.get to return mock response object
        # Mock _csrf_token to predictable value
        with patch.object(self.manager, '_client', MagicMock()) as mock_client, \
             patch.object(mock_client, 'get', return_value=mock_response) as mock_get, \
             patch.object(self.manager, '_csrf_token', None):

            # Call method with IP of existing node, confirm returns mock config string
            response = self.manager.download_node_config_file_from_django('192.168.1.123')
            self.assertEqual(response, 'mock_config_file')

            # Confirm made correct GET request
            mock_get.assert_called_once_with(
                f'{self.manager.config["django_backend"]}/get_node_config/192.168.1.123',
                timeout=5
            )

    def test_download_node_config_file_from_django_missing_config(self):
        # Create mock response object to simulate config missing from backend
        mock_response = MagicMock()
        mock_response.status_code = 404

        # Mock _client.get to return mock response object
        # Mock _csrf_token to predictable value
        with patch.object(self.manager, '_client', MagicMock()) as mock_client, \
             patch.object(mock_client, 'get', return_value=mock_response) as mock_get, \
             patch.object(self.manager, '_csrf_token', None):

            # Call method with IP of existing node, confirm returns False
            self.assertFalse(
                self.manager.download_node_config_file_from_django('192.168.1.123')
            )

    def test_download_node_config_file_from_django_no_backend_configured(self):
        with self.assertRaises(RuntimeError):
            # Mock CliConfigManager.config to an empty dict (no django_backend key)
            # Mock _client.get to confirm no request is made
            with patch.object(self.manager, 'config', {}), \
                 patch.object(self.manager, '_client', MagicMock()) as mock_client, \
                 patch.object(mock_client, 'get') as mock_get:

                # Call sync method, confirm no request was made
                self.manager.download_node_config_file_from_django('192.168.1.123')
                mock_get.assert_not_called()

    def test_download_all_node_config_files_from_django(self):
        # Mock download_node_config_file_from_django method to confirm arguments
        # Mock save_node_config_file method to confirm arguments
        with patch.object(self.manager, 'download_node_config_file_from_django') as mock_download, \
             patch.object(self.manager, 'save_node_config_file') as mock_save_config:

            # Call method
            self.manager.download_all_node_config_files_from_django()

            # Confirm both methods were called 3 times
            self.assertEqual(mock_download.call_count, 3)
            self.assertEqual(mock_save_config.call_count, 3)

            # Confirm download method was called with IP of each existing node
            self.assertEqual(mock_download.call_args_list[0][0][0], '192.168.1.123')
            self.assertEqual(mock_download.call_args_list[1][0][0], '192.168.1.234')
            self.assertEqual(mock_download.call_args_list[2][0][0], '192.168.1.111')

    def test_download_all_node_config_files_from_django_missing_configs(self):
        # Mock download_node_config_file_from_django method to return False (missing from backend)
        # Mock save_node_config_file method to confirm arguments
        with patch.object(self.manager, 'download_node_config_file_from_django', return_value=False) as mock_download, \
             patch.object(self.manager, 'save_node_config_file') as mock_save_config:

            # Call method
            self.manager.download_all_node_config_files_from_django()

            # Confirm download called 3 times, save called 0 (did not receive configs)
            self.assertEqual(mock_download.call_count, 3)
            self.assertEqual(mock_save_config.call_count, 0)

    def test_download_all_node_config_files_from_django_no_backend_configured(self):
        with self.assertRaises(RuntimeError):
            # Mock CliConfigManager.config to an empty dict (no django_backend key)
            # Mock download_node_config_file_from_django to confirm not called
            with patch.object(self.manager, 'config', {}), \
                 patch.object(self.manager, 'download_node_config_file_from_django') as mock_download:

                # Call method, confirm download_node_config_file_from_django was not called
                self.manager.download_all_node_config_files_from_django()
                mock_download.assert_not_called()

    def test_set_django_address(self):
        # Call method to change django address
        self.manager.set_django_address('http://10.0.0.1:9999')

        # Confirm changed in class attribute and on disk
        self.assertEqual(
            self.manager.config['django_backend'],
            'http://10.0.0.1:9999'
        )
        with open(mock_cli_config_path, 'r') as file:
            config = json.load(file)
        self.assertEqual(config['django_backend'], 'http://10.0.0.1:9999')

        # Call method again to change back
        self.manager.set_django_address('http://192.168.1.100')

        # Confirm changed back in class attribute and on disk
        self.assertEqual(
            self.manager.config['django_backend'],
            'http://192.168.1.100'
        )
        with open(mock_cli_config_path, 'r') as file:
            config = json.load(file)
        self.assertEqual(config['django_backend'], 'http://192.168.1.100')

    def test_set_config_directory(self):
        # Call method to change config_directory
        self.manager.set_config_directory('/fake/config/path')

        # Confirm changed in class attribute and on disk
        self.assertEqual(
            self.manager.config['config_directory'],
            '/fake/config/path'
        )
        with open(mock_cli_config_path, 'r') as file:
            config = json.load(file)
        self.assertEqual(config['config_directory'], '/fake/config/path')

        # Call method again to change back
        self.manager.set_config_directory(mock_config_dir)

        # Confirm changed back in class attribute and on disk
        self.assertEqual(
            self.manager.config['config_directory'],
            mock_config_dir
        )
        with open(mock_cli_config_path, 'r') as file:
            config = json.load(file)
        self.assertEqual(config['config_directory'], mock_config_dir)

    def test_set_webrepl_password(self):
        # Call method to change password
        self.manager.set_webrepl_password('newpass')

        # Confirm changed in class attribute and on disk
        self.assertEqual(self.manager.config['webrepl_password'], 'newpass')
        with open(mock_cli_config_path, 'r') as file:
            config = json.load(file)
        self.assertEqual(config['webrepl_password'], 'newpass')

        # Call method again to change back
        self.manager.set_webrepl_password('password')

        # Confirm changed back in class attribute and on disk
        self.assertEqual(self.manager.config['webrepl_password'], 'password')
        with open(mock_cli_config_path, 'r') as file:
            config = json.load(file)
        self.assertEqual(config['webrepl_password'], 'password')
