# pylint: disable=line-too-long, missing-function-docstring, missing-module-docstring, missing-class-docstring

import os
import json
from copy import deepcopy
from unittest import TestCase
from unittest.mock import patch, MagicMock, call
import requests
from requests.exceptions import ConnectionError
from cli_config_manager import (
    CliConfigManager,
    get_system_config_directory,
    get_app_config_directory,
    get_cli_config_path,
    get_default_cli_config
)
from mock_cli_config import (
    mock_cli_config,
    mock_cli_config_path,
    mock_config_dir
)


class TestGetFilesystemPaths(TestCase):
    '''Test functions used to get paths to files and directories inside
    platform-dependent system config directory (eg ~/.config).
    '''

    def test_get_system_config_directory(self):
        # Expected output for each platform
        windows = 'C:\\Users\\TestUser\\AppData\\Roaming'
        xdg_config_home = '/home/testuser/.config'
        unix_home = '/home/testuser'

        # Simulate windows env var, confirm expected path returned
        with patch(
            'os.environ',
            {'APPDATA': windows, 'XDG_CONFIG_HOME': None, 'HOME': None}
        ):
            self.assertEqual(get_system_config_directory(), windows)

        # Simulate XDG_CONFIG_HOME env var, confirm expected path returned
        with patch(
            'os.environ',
            {'APPDATA': None, 'XDG_CONFIG_HOME': xdg_config_home, 'HOME': None}
        ):
            self.assertEqual(get_system_config_directory(), xdg_config_home)

        # Simulate HOME env var, confirm expected path returned
        with patch(
            'os.environ',
            {'APPDATA': None, 'XDG_CONFIG_HOME': None, 'HOME': unix_home}
        ):
            self.assertEqual(
                get_system_config_directory(),
                os.path.join(unix_home, '.config')
            )

    def test_get_app_config_directory(self):
        # Mock path returned by get_system_config_directory
        # Mock os.path.exists to simulate directory already exists
        # Mock os.mkdir to confirm no directory created
        config_dir = '/home/test/.config'
        with patch('cli_config_manager.get_system_config_directory', return_value=config_dir), \
             patch('os.path.exists', return_value=True), \
             patch('os.mkdir') as mock_mkdir:

            # Confirm returns expected path
            self.assertEqual(
                get_app_config_directory(),
                '/home/test/.config/smarthome_cli'
            )

            # Confirm did NOT create directory (already exists)
            mock_mkdir.assert_not_called()

        # Mock path returned by get_system_config_directory
        # Mock os.path.exists to simulate directory does not exist
        # Mock os.mkdir to confirm directory was created
        config_dir = '/home/test/.config'
        with patch('cli_config_manager.get_system_config_directory', return_value=config_dir), \
             patch('os.path.exists', return_value=False), \
             patch('os.mkdir') as mock_mkdir:

            # Confirm returns expected path
            self.assertEqual(
                get_app_config_directory(),
                '/home/test/.config/smarthome_cli'
            )

            # Confirm created missing directory
            mock_mkdir.assert_called_once_with('/home/test/.config/smarthome_cli')

    def test_get_cli_config_path(self):
        # Mock path returned by get_app_config_directory
        with patch(
            'cli_config_manager.get_app_config_directory',
            return_value='/home/test/.config/smarthome_cli'
        ):
            # Confirm returns expected path
            self.assertEqual(
                get_cli_config_path(),
                '/home/test/.config/smarthome_cli/cli_config.json'
            )

    def test_get_default_cli_config(self):
        # Mock path returned by get_app_config_directory
        # Mock os.path.exists to simulate directory does not exist
        # Mock os.mkdir to confirm directory was created
        app_dir = '/home/test/.config/smarthome_cli'
        config_dir = '/home/test/.config/smarthome_cli/config_files'
        with patch('cli_config_manager.get_app_config_directory', return_value=app_dir), \
             patch('os.path.exists', return_value=False), \
             patch('os.mkdir') as mock_mkdir:

            # Confirm returns expected object
            self.assertEqual(
                get_default_cli_config(),
                {
                    'nodes': {},
                    'schedule_keywords': {},
                    'webrepl_password': 'password',
                    'config_directory': config_dir
                }
            )

            # Confirm created missing directory
            mock_mkdir.assert_called_once_with(config_dir)

        # Mock path returned by get_app_config_directory
        # Mock os.path.exists to simulate directory already exists
        # Mock os.mkdir to confirm directory was NOT created
        app_dir = '/home/test/.config/smarthome_cli'
        config_dir = '/home/test/.config/smarthome_cli/config_files'
        with patch('cli_config_manager.get_app_config_directory', return_value=app_dir), \
             patch('os.path.exists', return_value=True), \
             patch('os.mkdir') as mock_mkdir:

            # Confirm returns expected object
            self.assertEqual(
                get_default_cli_config(),
                {
                    'nodes': {},
                    'schedule_keywords': {},
                    'webrepl_password': 'password',
                    'config_directory': config_dir
                }
            )

            # Confirm did NOT create directory
            mock_mkdir.assert_not_called()


class TestCliConfigManager(TestCase):
    def setUp(self):
        # Mock path to cli_config.json (prevent overwriting real file)
        self.cli_config_patch = patch(
            'cli_config_manager.get_cli_config_path',
            return_value=mock_cli_config_path
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
             patch.object(mock_client, 'get', side_effect=ConnectionError), \
             patch.object(self.manager, 'write_cli_config_to_disk') as mock_write_to_disk:

            # Call sync method, confirm write_cli_config_to_disk was NOT called
            self.manager.sync_from_django()
            mock_write_to_disk.assert_not_called()

        # Create mock response object with bad status code
        mock_response = MagicMock()
        mock_response.status_code = 404

        # Mock _client.get to return mock response object
        with patch.object(self.manager, '_client', MagicMock()) as mock_client, \
             patch.object(mock_client, 'get', return_value=mock_response), \
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
        self.assertNotIn('new', self.manager.config['nodes'])

        # Confirm expected name does not exist in config_directory
        self.assertFalse(os.path.exists(os.path.join(mock_config_dir, 'new.json')))

        # Mock _client.post to return mock response object
        # Mock load_node_config_file to return empty dict (mock config json)
        # Mock _csrf_token to predictable value
        with patch.object(self.manager, '_client', MagicMock()) as mock_client, \
             patch.object(mock_client, 'post', return_value=mock_response) as mock_post, \
             patch.object(self.manager, 'load_node_config_file', return_value={}), \
             patch.object(self.manager, '_csrf_token', None):

            # Call add_node method with mock config dict
            self.manager.add_node({'metadata': {'id': 'New'}}, '192.168.1.63')

            # Confirm node was added to manager config attribute and file on disk
            self.assertIn('new', self.manager.config['nodes'])
            with open(mock_cli_config_path, 'r', encoding='utf-8') as file:
                config = json.load(file)
            self.assertIn('new', config['nodes'])

            # Confirm new node was posted to django backend
            mock_post.assert_called_once_with(
                f'{self.manager.config["django_backend"]}/add_node',
                json={
                    'ip': '192.168.1.63',
                    'config': {'metadata': {'id': 'New'}}
                },
                headers={
                    'X-CSRFToken': None
                },
                timeout=5
            )

        # Confirm mock config was written to config_directory
        self.assertTrue(os.path.exists(os.path.join(mock_config_dir, 'new.json')))

    def test_add_node_no_backend_configured(self):
        # Confirm config object does not contain name that will be added
        self.assertNotIn('new', self.manager.config['nodes'])

        # Confirm expected name does not exist in config_directory
        self.assertFalse(os.path.exists(os.path.join(mock_config_dir, 'new.json')))

        # Create mock cli_config.json with no django backend configured
        mock_cli_config_no_backend = deepcopy(mock_cli_config)
        del mock_cli_config_no_backend['django_backend']

        # Mock CliConfigManager.config remove django_backend key
        # Mock _client.post to confirm no request is made
        with patch.object(self.manager, 'config', mock_cli_config_no_backend), \
             patch.object(self.manager, '_client', MagicMock()) as mock_client, \
             patch.object(mock_client, 'post') as mock_post:

            # Call add_node method with mock config dict
            self.manager.add_node({'metadata': {'id': 'New'}}, '192.168.1.63')

            # Confirm node was added to manager config attribute and file on disk
            self.assertIn('new', self.manager.config['nodes'])
            with open(mock_cli_config_path, 'r', encoding='utf-8') as file:
                config = json.load(file)
            self.assertIn('new', config['nodes'])

            # Confirm no POST request was made
            mock_post.assert_not_called()

        # Confirm mock config was written to config_directory
        self.assertTrue(os.path.exists(os.path.join(mock_config_dir, 'new.json')))

    def test_add_node_backend_offline(self):
        # Create mock response object
        mock_response = MagicMock()
        mock_response.status_code = 200

        # Confirm config object does not contain name that will be added
        self.assertNotIn('new', self.manager.config['nodes'])

        # Confirm expected name does not exist in config_directory
        self.assertFalse(os.path.exists(os.path.join(mock_config_dir, 'new.json')))

        # Mock _client.post to raise ConnectionError (simulate backend offline)
        # Mock load_node_config_file to return empty dict (mock config json)
        # Mock _csrf_token to predictable value
        # Mock print to confirm correct error printed
        with patch.object(self.manager, '_client', MagicMock()) as mock_client, \
             patch.object(mock_client, 'post', side_effect=ConnectionError) as mock_post, \
             patch.object(self.manager, 'load_node_config_file', return_value={}), \
             patch.object(self.manager, '_csrf_token', None), \
             patch('builtins.print') as mock_print:

            # Call add_node method with mock config dict
            self.manager.add_node({'metadata': {'id': 'New'}}, '192.168.1.63')

            # Confirm node was added to manager config attribute and file on disk
            self.assertIn('new', self.manager.config['nodes'])
            with open(mock_cli_config_path, 'r', encoding='utf-8') as file:
                config = json.load(file)
            self.assertIn('new', config['nodes'])

            # Confirm new node was posted to django backend
            mock_post.assert_called_once_with(
                f'{self.manager.config["django_backend"]}/add_node',
                json={
                    'ip': '192.168.1.63',
                    'config': {'metadata': {'id': 'New'}}
                },
                headers={
                    'X-CSRFToken': None
                },
                timeout=5
            )

            # Confirm printed error when django request failed
            mock_print.assert_called_with(
                'Failed to add to django database (connection error)'
            )

        # Confirm mock config was written to config_directory
        self.assertTrue(os.path.exists(os.path.join(mock_config_dir, 'new.json')))

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
            with open(mock_cli_config_path, 'r', encoding='utf-8') as file:
                config = json.load(file)
            self.assertNotIn('node3', config['nodes'])

            # Confirm delete_node payload was posted to django backend
            mock_post.assert_called_once_with(
                f'{self.manager.config["django_backend"]}/delete_node',
                json={'ip': '192.168.1.111'},
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
            with open(mock_cli_config_path, 'r', encoding='utf-8') as file:
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

    def test_remove_node_backend_offline(self):
        # Confirm config object contains node3
        self.assertIn('node3', self.manager.config['nodes'])

        # Mock _client.post to confirm not called
        # Mock os.path.exists to return False (config missing from disk)
        with patch.object(self.manager, '_client', MagicMock()) as mock_client, \
             patch.object(mock_client, 'post', side_effect=ConnectionError) as mock_post, \
             patch.object(self.manager, '_csrf_token', None), \
             patch('builtins.print') as mock_print:

            # Call remove_node method with name of existing node
            self.manager.remove_node('node3')

            # Confirm node3 was removed from manager config attribute and file on disk
            self.assertNotIn('node3', self.manager.config['nodes'])
            with open(mock_cli_config_path, 'r', encoding='utf-8') as file:
                config = json.load(file)
            self.assertNotIn('node3', config['nodes'])

            # Confirm delete_node payload was posted to django backend
            mock_post.assert_called_once_with(
                f'{self.manager.config["django_backend"]}/delete_node',
                json={'ip': '192.168.1.111'},
                headers={
                    'X-CSRFToken': None
                },
                timeout=5
            )

            # Confirm printed error when django request failed
            mock_print.assert_called_with(
                'Failed to delete from django database (connection error)'
            )

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
             patch.object(mock_client, 'post', return_value=mock_response), \
             patch.object(self.manager, '_csrf_token', None), \
             patch('builtins.print') as mock_print:

            # Call remove_node method with name of existing node
            self.manager.remove_node('node3')

            # Confirm node3 was removed from manager config attribute and file on disk
            self.assertNotIn('node3', self.manager.config['nodes'])
            with open(mock_cli_config_path, 'r', encoding='utf-8') as file:
                config = json.load(file)
            self.assertNotIn('node3', config['nodes'])

            # Confirm printed backend error response to console
            mock_print.assert_called_with('Failed to delete Node3, does not exist')

    def test_change_node_ip(self):
        # Create mock response object
        mock_response = MagicMock()
        mock_response.status_code = 200

        # Confirm node3 has expected IP in config object
        self.assertEqual(self.manager.config['nodes']['node3'], '192.168.1.111')

        # Mock provision to return success object
        # Mock get_modules to return predictable value
        # Mock _client.post to return mock response object
        # Mock _csrf_token to predictable value
        with patch('cli_config_manager.provision', return_value={'status': 200}) as mock_provision, \
             patch('cli_config_manager.get_modules', return_value=['module']), \
             patch.object(self.manager, '_client', MagicMock()) as mock_client, \
             patch.object(mock_client, 'post', return_value=mock_response) as mock_post, \
             patch.object(self.manager, '_csrf_token', None):

            # Call change_node_ip method with name of existing node and new IP
            self.manager.change_node_ip('node3', '192.168.1.222')

            # Confirm provision was called with expected arguments
            mock_provision.assert_called_once_with(
                ip='192.168.1.222',
                password=self.manager.config['webrepl_password'],
                config={'metadata': {'id': 'Node3'}},
                modules=['module']
            )

            # Confirm correct POST request was sent to django backend
            mock_post.assert_called_once_with(
                f'{self.manager.config["django_backend"]}/change_node_ip',
                json={
                    'friendly_name': 'Node3',
                    'new_ip': '192.168.1.222',
                    'reupload': False
                },
                headers={
                    'X-CSRFToken': None
                },
                timeout=5
            )

            # Confirm IP changed in manager config and file on disk
            self.assertEqual(self.manager.config['nodes']['node3'], '192.168.1.222')
            with open(mock_cli_config_path, 'r', encoding='utf-8') as file:
                config = json.load(file)
            self.assertEqual(config['nodes']['node3'], '192.168.1.222')

    def test_change_node_ip_reupload_failed(self):
        # Create mock provision response object simulating offline node
        mock_response = {
            'message': 'Error: Unable to connect to node, please make sure it is connected to wifi and try again.',
            'status': 404
        }

        # Confirm node3 has expected IP in config object
        self.assertEqual(self.manager.config['nodes']['node3'], '192.168.1.111')

        # Mock provision to return provision response object (error)
        # Mock get_modules to return predictable value
        # Mock _client.post to confirm not called
        # Mock print to confirm correct error was printed
        with patch('cli_config_manager.provision', return_value=mock_response) as mock_provision, \
             patch('cli_config_manager.get_modules', return_value=['module']), \
             patch.object(self.manager, '_client', MagicMock()) as mock_client, \
             patch.object(mock_client, 'post', return_value=mock_response) as mock_post, \
             patch('builtins.print') as mock_print:

            # Call change_node_ip method with name of existing node and new IP
            self.manager.change_node_ip('node3', '192.168.1.222')

            # Confirm provision was called with expected arguments
            mock_provision.assert_called_once_with(
                ip='192.168.1.222',
                password=self.manager.config['webrepl_password'],
                config={'metadata': {'id': 'Node3'}},
                modules=['module']
            )

            # Confirm no request was sent to backend
            mock_post.assert_not_called()

            # Confirm IP did NOT change in manager config or file on disk
            self.assertEqual(self.manager.config['nodes']['node3'], '192.168.1.111')
            with open(mock_cli_config_path, 'r', encoding='utf-8') as file:
                config = json.load(file)
            self.assertEqual(config['nodes']['node3'], '192.168.1.111')

            # Confirm provision error was printed
            mock_print.assert_called_with(
                'Error: Unable to connect to node, please make sure it is connected to wifi and try again.'
            )

    def test_change_node_ip_django_request_failed(self):
        # Create mock response object simulating failed django request
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = 'New IP must be different than old'

        # Confirm node3 has expected IP in config object
        self.assertEqual(self.manager.config['nodes']['node3'], '192.168.1.111')

        # Mock provision to return success object
        # Mock get_modules to return predictable value
        # Mock _client.post to return mock error response object
        # Mock _csrf_token to predictable value
        # Mock print to confirm correct error was printed
        with patch('cli_config_manager.provision', return_value={'status': 200}) as mock_provision, \
             patch('cli_config_manager.get_modules', return_value=['module']), \
             patch.object(self.manager, '_client', MagicMock()) as mock_client, \
             patch.object(mock_client, 'post', return_value=mock_response) as mock_post, \
             patch.object(self.manager, '_csrf_token', None), \
             patch('builtins.print') as mock_print:

            # Call change_node_ip method with name of existing node and new IP
            self.manager.change_node_ip('node3', '192.168.1.222')

            # Confirm provision was called with expected arguments
            mock_provision.assert_called_once_with(
                ip='192.168.1.222',
                password=self.manager.config['webrepl_password'],
                config={'metadata': {'id': 'Node3'}},
                modules=['module']
            )

            # Confirm correct POST request was sent to django backend
            mock_post.assert_called_once_with(
                f'{self.manager.config["django_backend"]}/change_node_ip',
                json={
                    'friendly_name': 'Node3',
                    'new_ip': '192.168.1.222',
                    'reupload': False
                },
                headers={
                    'X-CSRFToken': None
                },
                timeout=5
            )

            # Confirm IP changed in manager config and file on disk
            self.assertEqual(self.manager.config['nodes']['node3'], '192.168.1.222')
            with open(mock_cli_config_path, 'r', encoding='utf-8') as file:
                config = json.load(file)
            self.assertEqual(config['nodes']['node3'], '192.168.1.222')

            # Confirm django error was printed
            mock_print.assert_called_with('New IP must be different than old')

    def test_change_node_ip_no_django(self):
        # Confirm node3 has expected IP in config object
        self.assertEqual(self.manager.config['nodes']['node3'], '192.168.1.111')

        # Create mock cli_config.json with no django backend configured
        mock_cli_config_no_backend = deepcopy(mock_cli_config)
        del mock_cli_config_no_backend['django_backend']

        # Mock provision to return success object
        # Mock get_modules to return predictable value
        # Mock _client.post to confirm not called
        # Mock cli_config.json to simulate no django backend
        with patch('cli_config_manager.provision', return_value={'status': 200}) as mock_provision, \
             patch('cli_config_manager.get_modules', return_value=['module']), \
             patch.object(self.manager, '_client', MagicMock()) as mock_client, \
             patch.object(mock_client, 'post') as mock_post, \
             patch('smarthome_cli.cli_config.config', mock_cli_config_no_backend):

            # Call change_node_ip method with name of existing node and new IP
            self.manager.change_node_ip('node3', '192.168.1.222')

            # Confirm provision was called with expected arguments
            mock_provision.assert_called_once_with(
                ip='192.168.1.222',
                password=self.manager.config['webrepl_password'],
                config={'metadata': {'id': 'Node3'}},
                modules=['module']
            )

            # Confirm did NOT make POST request (no django backend configured)
            mock_post.assert_not_called()

            # Confirm IP changed in manager config and file on disk
            self.assertEqual(self.manager.config['nodes']['node3'], '192.168.1.222')
            with open(mock_cli_config_path, 'r', encoding='utf-8') as file:
                config = json.load(file)
            self.assertEqual(config['nodes']['node3'], '192.168.1.222')

    def test_change_node_ip_django_backend_offline(self):
        # Confirm node3 has expected IP in config object
        self.assertEqual(self.manager.config['nodes']['node3'], '192.168.1.111')

        # Mock provision to return success object
        # Mock get_modules to return predictable value
        # Mock _client.post to raise ConnectionError (simulate offline backend)
        # Mock _csrf_token to predictable value
        # Mock print to confirm correct error was printed
        with patch('cli_config_manager.provision', return_value={'status': 200}) as mock_provision, \
             patch('cli_config_manager.get_modules', return_value=['module']), \
             patch.object(self.manager, '_client', MagicMock()) as mock_client, \
             patch.object(mock_client, 'post', side_effect=ConnectionError) as mock_post, \
             patch.object(self.manager, '_csrf_token', None), \
             patch('builtins.print') as mock_print:

            # Call change_node_ip method with name of existing node and new IP
            self.manager.change_node_ip('node3', '192.168.1.222')

            # Confirm provision was called with expected arguments
            mock_provision.assert_called_once_with(
                ip='192.168.1.222',
                password=self.manager.config['webrepl_password'],
                config={'metadata': {'id': 'Node3'}},
                modules=['module']
            )

            # Confirm correct POST request was sent to django backend
            mock_post.assert_called_once_with(
                f'{self.manager.config["django_backend"]}/change_node_ip',
                json={
                    'friendly_name': 'Node3',
                    'new_ip': '192.168.1.222',
                    'reupload': False
                },
                headers={
                    'X-CSRFToken': None
                },
                timeout=5
            )

            # Confirm IP changed in manager config and file on disk
            self.assertEqual(self.manager.config['nodes']['node3'], '192.168.1.222')
            with open(mock_cli_config_path, 'r', encoding='utf-8') as file:
                config = json.load(file)
            self.assertEqual(config['nodes']['node3'], '192.168.1.222')

            # Confirm correct error was printed
            mock_print.assert_called_with(
                'Failed to update django database (connection error)'
            )

    def test_change_node_ip_unable_to_find_config_file(self):
        # Confirm node3 has expected IP in config object
        self.assertEqual(self.manager.config['nodes']['node3'], '192.168.1.111')

        # Mock provision, _client.post to confirm not called
        # Mock load_node_config_file to raise FileNotFoundError (raised when
        # unable to get config for any reason - doesn't exist and no backend,
        # user declined to download from backend, connection to backend failed)
        with patch('cli_config_manager.provision') as mock_provision, \
             patch('cli_config_manager.get_modules'), \
             patch.object(self.manager, '_client', MagicMock()) as mock_client, \
             patch.object(mock_client, 'post') as mock_post, \
             patch.object(self.manager, 'load_node_config_file', side_effect=FileNotFoundError):

            # Call change_node_ip method with name of existing node and new IP
            self.manager.change_node_ip('node3', '192.168.1.222')

            # Confirm provision, _client.post were NOT called
            mock_provision.assert_not_called()
            mock_post.assert_not_called()

            # Confirm node3 IP did not change in config object
            self.assertEqual(self.manager.config['nodes']['node3'], '192.168.1.111')

    def test_add_schedule_keyword(self):
        # Confirm config does not contain NewName keyword
        self.assertNotIn('NewName', self.manager.config['schedule_keywords'])

        # Create mock django response object
        mock_response = MagicMock()
        mock_response.status_code = 200

        # Mock endpoints called by bulk API call functions
        # Mock _client.post to confirm correct request made to django backend
        with patch('api_helper_functions.add_schedule_keyword') as mock_add_keyword, \
             patch('api_helper_functions.save_schedule_keywords') as mock_save_keywords, \
             patch.object(self.manager, '_client', MagicMock()) as mock_client, \
             patch.object(mock_client, 'post', return_value=mock_response) as mock_post, \
             patch.object(self.manager, '_csrf_token', None):

            # Call add_schedule_keyword with new keyword name and timestamp
            self.manager.add_schedule_keyword('NewName', '12:34')

            # Confirm added to manager config and file on disk
            self.assertIn('NewName', self.manager.config['schedule_keywords'])
            self.assertEqual(self.manager.config['schedule_keywords']['NewName'], '12:34')
            with open(mock_cli_config_path, 'r', encoding='utf-8') as file:
                config = json.load(file)
            self.assertIn('NewName', config['schedule_keywords'])
            self.assertEqual(config['schedule_keywords']['NewName'], '12:34')

            # Confirm add_schedule_keyword endpoint was called once for each node
            self.assertEqual(mock_add_keyword.call_count, 3)
            expected_calls = [
                call('192.168.1.123', ['NewName', '12:34']),
                call('192.168.1.234', ['NewName', '12:34']),
                call('192.168.1.111', ['NewName', '12:34']),
            ]
            self.assertCountEqual(mock_add_keyword.call_args_list, expected_calls)

            # Confirm save_schedule_keywords endpoint was called once for each node
            self.assertEqual(mock_save_keywords.call_count, 3)
            expected_calls = [
                call('192.168.1.123', ''),
                call('192.168.1.234', ''),
                call('192.168.1.111', ''),
            ]
            self.assertCountEqual(mock_save_keywords.call_args_list, expected_calls)

            # Confirm new keyword was posted to django backend
            mock_post.assert_called_once_with(
                f'{self.manager.config["django_backend"]}/add_schedule_keyword',
                json={
                    'keyword': 'NewName',
                    'timestamp': '12:34',
                    'sync_nodes': False
                },
                headers={
                    'X-CSRFToken': None
                },
                timeout=5
            )

    def test_add_schedule_keyword_no_django(self):
        # Confirm config does not contain NewName keyword
        self.assertNotIn('NewName', self.manager.config['schedule_keywords'])

        # Create mock cli_config.json with no django backend configured
        mock_cli_config_no_backend = deepcopy(mock_cli_config)
        del mock_cli_config_no_backend['django_backend']

        # Mock endpoints called by bulk API call functions
        # Mock _client.post to confirm no request made
        # Mock cli_config.json to simulate no django backend
        with patch('api_helper_functions.add_schedule_keyword') as mock_add_keyword, \
             patch('api_helper_functions.save_schedule_keywords') as mock_save_keywords, \
             patch.object(self.manager, '_client', MagicMock()) as mock_client, \
             patch.object(mock_client, 'post') as mock_post, \
             patch.object(self.manager, 'config', mock_cli_config_no_backend):

            # Call add_schedule_keyword with new keyword name and timestamp
            self.manager.add_schedule_keyword('NewName', '12:34')

            # Confirm added to manager config and file on disk
            self.assertIn('NewName', self.manager.config['schedule_keywords'])
            self.assertEqual(self.manager.config['schedule_keywords']['NewName'], '12:34')
            with open(mock_cli_config_path, 'r', encoding='utf-8') as file:
                config = json.load(file)
            self.assertIn('NewName', config['schedule_keywords'])
            self.assertEqual(config['schedule_keywords']['NewName'], '12:34')

            # Confirm add_schedule_keyword and save_schedule_keywords endpoints
            # were called once for each node
            self.assertEqual(mock_add_keyword.call_count, 3)
            self.assertEqual(mock_save_keywords.call_count, 3)

            # Confirm no POST request was made
            mock_post.assert_not_called()

    def test_add_schedule_keyword_backend_offline(self):
        # Confirm config does not contain NewName keyword
        self.assertNotIn('NewName', self.manager.config['schedule_keywords'])

        # Mock endpoints called by bulk API call functions
        # Mock _client.post to raise ConnectionError (simulate offline backend)
        # Mock print to confirm correct error was printed
        with patch('api_helper_functions.add_schedule_keyword') as mock_add_keyword, \
             patch('api_helper_functions.save_schedule_keywords') as mock_save_keywords, \
             patch.object(self.manager, '_client', MagicMock()) as mock_client, \
             patch.object(mock_client, 'post', side_effect=ConnectionError) as mock_post, \
             patch.object(self.manager, '_csrf_token', None), \
             patch('builtins.print') as mock_print:

            # Call add_schedule_keyword with new keyword name and timestamp
            self.manager.add_schedule_keyword('NewName', '12:34')

            # Confirm added to manager config and file on disk
            self.assertIn('NewName', self.manager.config['schedule_keywords'])
            self.assertEqual(self.manager.config['schedule_keywords']['NewName'], '12:34')
            with open(mock_cli_config_path, 'r', encoding='utf-8') as file:
                config = json.load(file)
            self.assertIn('NewName', config['schedule_keywords'])
            self.assertEqual(config['schedule_keywords']['NewName'], '12:34')

            # Confirm add_schedule_keyword endpoint was called once for each node
            self.assertEqual(mock_add_keyword.call_count, 3)
            expected_calls = [
                call('192.168.1.123', ['NewName', '12:34']),
                call('192.168.1.234', ['NewName', '12:34']),
                call('192.168.1.111', ['NewName', '12:34']),
            ]
            self.assertCountEqual(mock_add_keyword.call_args_list, expected_calls)

            # Confirm save_schedule_keywords endpoint was called once for each node
            self.assertEqual(mock_save_keywords.call_count, 3)
            expected_calls = [
                call('192.168.1.123', ''),
                call('192.168.1.234', ''),
                call('192.168.1.111', ''),
            ]
            self.assertCountEqual(mock_save_keywords.call_args_list, expected_calls)

            # Confirm new keyword was posted to django backend
            mock_post.assert_called_once_with(
                f'{self.manager.config["django_backend"]}/add_schedule_keyword',
                json={
                    'keyword': 'NewName',
                    'timestamp': '12:34',
                    'sync_nodes': False
                },
                headers={
                    'X-CSRFToken': None
                },
                timeout=5
            )

            # Confirm correct error was printed
            mock_print.assert_called_with(
                'Failed to add to django database (connection error)'
            )

    def test_edit_schedule_keyword(self):
        # Confirm config contains sleep keyword, does not contain NewName
        self.assertIn('sleep', self.manager.config['schedule_keywords'])
        self.assertNotIn('NewName', self.manager.config['schedule_keywords'])

        # Create mock django response object
        mock_response = MagicMock()
        mock_response.status_code = 200

        # Mock endpoints called by bulk API call functions
        # Mock _client.post to confirm correct request made to django backend
        with patch('api_helper_functions.add_schedule_keyword') as mock_add_keyword, \
             patch('api_helper_functions.remove_schedule_keyword') as mock_rm_keyword, \
             patch('api_helper_functions.save_schedule_keywords') as mock_save_keywords, \
             patch.object(self.manager, '_client', MagicMock()) as mock_client, \
             patch.object(mock_client, 'post', return_value=mock_response) as mock_post, \
             patch.object(self.manager, '_csrf_token', None):

            # Call edit_schedule_keyword with existing keyword name, new name,
            # new timestamp
            self.manager.edit_schedule_keyword('sleep', 'NewName', '12:34')

            # Confirm manager config no longer contains sleep, does contain NewName
            self.assertNotIn('sleep', self.manager.config['schedule_keywords'])
            self.assertIn('NewName', self.manager.config['schedule_keywords'])
            self.assertEqual(self.manager.config['schedule_keywords']['NewName'], '12:34')

            # Confirm file on disk no longer contains sleep, does contain NewName
            with open(mock_cli_config_path, 'r', encoding='utf-8') as file:
                config = json.load(file)
            self.assertNotIn('sleep', config['schedule_keywords'])
            self.assertIn('NewName', config['schedule_keywords'])
            self.assertEqual(config['schedule_keywords']['NewName'], '12:34')

            # Confirm remove_schedule_keyword endpoint was called once for each node
            self.assertEqual(mock_rm_keyword.call_count, 3)
            expected_calls = [
                call('192.168.1.123', ['sleep']),
                call('192.168.1.234', ['sleep']),
                call('192.168.1.111', ['sleep']),
            ]
            self.assertCountEqual(mock_rm_keyword.call_args_list, expected_calls)

            # Confirm add_schedule_keyword endpoint was called once for each node
            self.assertEqual(mock_add_keyword.call_count, 3)
            expected_calls = [
                call('192.168.1.123', ['NewName', '12:34']),
                call('192.168.1.234', ['NewName', '12:34']),
                call('192.168.1.111', ['NewName', '12:34']),
            ]
            self.assertCountEqual(mock_add_keyword.call_args_list, expected_calls)

            # Confirm save_schedule_keywords endpoint was called once for each node
            self.assertEqual(mock_save_keywords.call_count, 3)
            expected_calls = [
                call('192.168.1.123', ''),
                call('192.168.1.234', ''),
                call('192.168.1.111', ''),
            ]
            self.assertCountEqual(mock_save_keywords.call_args_list, expected_calls)

            # Confirm new keyword was posted to django backend
            mock_post.assert_called_once_with(
                f'{self.manager.config["django_backend"]}/edit_schedule_keyword',
                json={
                    'keyword_old': 'sleep',
                    'keyword_new': 'NewName',
                    'timestamp_new': '12:34',
                    'sync_nodes': False
                },
                headers={
                    'X-CSRFToken': None
                },
                timeout=5
            )

    def test_edit_schedule_keyword_dont_change_name(self):
        # Confirm config contains sleep keyword, does not contain NewName
        self.assertIn('sleep', self.manager.config['schedule_keywords'])
        self.assertNotIn('NewName', self.manager.config['schedule_keywords'])

        # Create mock django response object
        mock_response = MagicMock()
        mock_response.status_code = 200

        # Mock endpoints called by bulk API call functions
        # Mock _client.post to confirm correct request made to django backend
        with patch('api_helper_functions.add_schedule_keyword') as mock_add_keyword, \
             patch('api_helper_functions.remove_schedule_keyword') as mock_rm_keyword, \
             patch('api_helper_functions.save_schedule_keywords') as mock_save_keywords, \
             patch.object(self.manager, '_client', MagicMock()) as mock_client, \
             patch.object(mock_client, 'post', return_value=mock_response) as mock_post, \
             patch.object(self.manager, '_csrf_token', None):

            # Call edit_schedule_keyword with same value for existing and new
            # keyword names, new timestamp
            self.manager.edit_schedule_keyword('sleep', 'sleep', '12:34')

            # Confirm sleep keyword timestamp changed in manager config
            self.assertIn('sleep', self.manager.config['schedule_keywords'])
            self.assertEqual(self.manager.config['schedule_keywords']['sleep'], '12:34')

            # Confirm sleep keyword timestamp changed in file on disk
            with open(mock_cli_config_path, 'r', encoding='utf-8') as file:
                config = json.load(file)
            self.assertIn('sleep', config['schedule_keywords'])
            self.assertEqual(config['schedule_keywords']['sleep'], '12:34')

            # Confirm remove_schedule_keyword endpoint was NOT called
            self.assertEqual(mock_rm_keyword.call_count, 0)

            # Confirm add_schedule_keyword endpoint was called once for each node
            self.assertEqual(mock_add_keyword.call_count, 3)
            expected_calls = [
                call('192.168.1.123', ['sleep', '12:34']),
                call('192.168.1.234', ['sleep', '12:34']),
                call('192.168.1.111', ['sleep', '12:34']),
            ]
            self.assertCountEqual(mock_add_keyword.call_args_list, expected_calls)

            # Confirm save_schedule_keywords endpoint was called once for each node
            self.assertEqual(mock_save_keywords.call_count, 3)
            expected_calls = [
                call('192.168.1.123', ''),
                call('192.168.1.234', ''),
                call('192.168.1.111', ''),
            ]
            self.assertCountEqual(mock_save_keywords.call_args_list, expected_calls)

            # Confirm new keyword was posted to django backend
            mock_post.assert_called_once_with(
                f'{self.manager.config["django_backend"]}/edit_schedule_keyword',
                json={
                    'keyword_old': 'sleep',
                    'keyword_new': 'sleep',
                    'timestamp_new': '12:34',
                    'sync_nodes': False
                },
                headers={
                    'X-CSRFToken': None
                },
                timeout=5
            )

    def test_edit_schedule_keyword_no_django(self):
        # Confirm config contains sleep keyword, does not contain NewName
        self.assertIn('sleep', self.manager.config['schedule_keywords'])
        self.assertNotIn('NewName', self.manager.config['schedule_keywords'])

        # Create mock cli_config.json with no django backend configured
        mock_cli_config_no_backend = deepcopy(mock_cli_config)
        del mock_cli_config_no_backend['django_backend']

        # Mock endpoints called by bulk API call functions
        # Mock _client.post to confirm no request made
        # Mock cli_config.json to simulate no django backend
        with patch('api_helper_functions.add_schedule_keyword') as mock_add_keyword, \
             patch('api_helper_functions.remove_schedule_keyword') as mock_rm_keyword, \
             patch('api_helper_functions.save_schedule_keywords') as mock_save_keywords, \
             patch.object(self.manager, '_client', MagicMock()) as mock_client, \
             patch.object(mock_client, 'post') as mock_post, \
             patch.object(self.manager, 'config', mock_cli_config_no_backend):

            # Call edit_schedule_keyword with existing keyword name, new name,
            # new timestamp
            self.manager.edit_schedule_keyword('sleep', 'NewName', '12:34')

            # Confirm manager config no longer contains sleep, does contain NewName
            self.assertNotIn('sleep', self.manager.config['schedule_keywords'])
            self.assertIn('NewName', self.manager.config['schedule_keywords'])
            self.assertEqual(self.manager.config['schedule_keywords']['NewName'], '12:34')

            # Confirm file on disk no longer contains sleep, does contain NewName
            with open(mock_cli_config_path, 'r', encoding='utf-8') as file:
                config = json.load(file)
            self.assertNotIn('sleep', config['schedule_keywords'])
            self.assertIn('NewName', config['schedule_keywords'])
            self.assertEqual(config['schedule_keywords']['NewName'], '12:34')

            # Confirm add_schedule_keyword, remove_schedule_keyword and
            # save_schedule_keywords endpoints were called once for each node
            self.assertEqual(mock_add_keyword.call_count, 3)
            self.assertEqual(mock_rm_keyword.call_count, 3)
            self.assertEqual(mock_save_keywords.call_count, 3)

            # Confirm no POST request was made
            mock_post.assert_not_called()

    def test_edit_schedule_keyword_backend_offline(self):
        # Confirm config contains sleep keyword, does not contain NewName
        self.assertIn('sleep', self.manager.config['schedule_keywords'])
        self.assertNotIn('NewName', self.manager.config['schedule_keywords'])

        # Mock endpoints called by bulk API call functions
        # Mock _client.post to raise ConnectionError (simulate offline backend)
        # Mock print to confirm correct error was printed
        with patch('api_helper_functions.add_schedule_keyword') as mock_add_keyword, \
             patch('api_helper_functions.remove_schedule_keyword') as mock_rm_keyword, \
             patch('api_helper_functions.save_schedule_keywords') as mock_save_keywords, \
             patch.object(self.manager, '_client', MagicMock()) as mock_client, \
             patch.object(mock_client, 'post', side_effect=ConnectionError) as mock_post, \
             patch.object(self.manager, '_csrf_token', None), \
             patch('builtins.print') as mock_print:

            # Call edit_schedule_keyword with same value for existing and new
            # keyword names, new timestamp
            self.manager.edit_schedule_keyword('sleep', 'sleep', '12:34')

            # Confirm sleep keyword timestamp changed in manager config
            self.assertIn('sleep', self.manager.config['schedule_keywords'])
            self.assertEqual(self.manager.config['schedule_keywords']['sleep'], '12:34')

            # Confirm sleep keyword timestamp changed in file on disk
            with open(mock_cli_config_path, 'r', encoding='utf-8') as file:
                config = json.load(file)
            self.assertIn('sleep', config['schedule_keywords'])
            self.assertEqual(config['schedule_keywords']['sleep'], '12:34')

            # Confirm remove_schedule_keyword endpoint was NOT called
            self.assertEqual(mock_rm_keyword.call_count, 0)

            # Confirm add_schedule_keyword endpoint was called once for each node
            self.assertEqual(mock_add_keyword.call_count, 3)
            expected_calls = [
                call('192.168.1.123', ['sleep', '12:34']),
                call('192.168.1.234', ['sleep', '12:34']),
                call('192.168.1.111', ['sleep', '12:34']),
            ]
            self.assertCountEqual(mock_add_keyword.call_args_list, expected_calls)

            # Confirm save_schedule_keywords endpoint was called once for each node
            self.assertEqual(mock_save_keywords.call_count, 3)
            expected_calls = [
                call('192.168.1.123', ''),
                call('192.168.1.234', ''),
                call('192.168.1.111', ''),
            ]
            self.assertCountEqual(mock_save_keywords.call_args_list, expected_calls)

            # Confirm new keyword was posted to django backend
            mock_post.assert_called_once_with(
                f'{self.manager.config["django_backend"]}/edit_schedule_keyword',
                json={
                    'keyword_old': 'sleep',
                    'keyword_new': 'sleep',
                    'timestamp_new': '12:34',
                    'sync_nodes': False
                },
                headers={
                    'X-CSRFToken': None
                },
                timeout=5
            )

            # Confirm correct error was printed
            mock_print.assert_called_with(
                'Failed to update django database (connection error)'
            )

    def test_remove_schedule_keyword(self):
        # Confirm config contains sleep keyword
        self.assertIn('sleep', self.manager.config['schedule_keywords'])

        # Create mock django response object
        mock_response = MagicMock()
        mock_response.status_code = 200

        # Mock endpoints called by bulk API call functions
        # Mock _client.post to confirm correct request made to django backend
        with patch('api_helper_functions.remove_schedule_keyword') as mock_rm_keyword, \
             patch('api_helper_functions.save_schedule_keywords') as mock_save_keywords, \
             patch.object(self.manager, '_client', MagicMock()) as mock_client, \
             patch.object(mock_client, 'post', return_value=mock_response) as mock_post, \
             patch.object(self.manager, '_csrf_token', None):

            # Call remove_schedule_keyword with existing keyword name
            self.manager.remove_schedule_keyword('sleep')

            # Confirm removed from manager config and file on disk
            self.assertNotIn('sleep', self.manager.config['schedule_keywords'])
            with open(mock_cli_config_path, 'r', encoding='utf-8') as file:
                config = json.load(file)
            self.assertNotIn('sleep', config['schedule_keywords'])

            # Confirm remove_schedule_keyword endpoint was called once for each node
            self.assertEqual(mock_rm_keyword.call_count, 3)
            expected_calls = [
                call('192.168.1.123', ['sleep']),
                call('192.168.1.234', ['sleep']),
                call('192.168.1.111', ['sleep']),
            ]
            self.assertCountEqual(mock_rm_keyword.call_args_list, expected_calls)

            # Confirm save_schedule_keywords endpoint was called once for each node
            self.assertEqual(mock_save_keywords.call_count, 3)
            expected_calls = [
                call('192.168.1.123', ''),
                call('192.168.1.234', ''),
                call('192.168.1.111', ''),
            ]
            self.assertCountEqual(mock_save_keywords.call_args_list, expected_calls)

            # Confirm keyword was removed from django backend
            mock_post.assert_called_once_with(
                f'{self.manager.config["django_backend"]}/delete_schedule_keyword',
                json={
                    'keyword': 'sleep',
                    'sync_nodes': False
                },
                headers={
                    'X-CSRFToken': None
                },
                timeout=5
            )

    def test_remove_schedule_keyword_no_django(self):
        # Confirm config contains sleep keyword
        self.assertIn('sleep', self.manager.config['schedule_keywords'])

        # Create mock cli_config.json with no django backend configured
        mock_cli_config_no_backend = deepcopy(mock_cli_config)
        del mock_cli_config_no_backend['django_backend']

        # Mock endpoints called by bulk API call functions
        # Mock _client.post to confirm no request made
        # Mock cli_config.json to simulate no django backend
        with patch('api_helper_functions.remove_schedule_keyword') as mock_rm_keyword, \
             patch('api_helper_functions.save_schedule_keywords') as mock_save_keywords, \
             patch.object(self.manager, '_client', MagicMock()) as mock_client, \
             patch.object(mock_client, 'post') as mock_post, \
             patch.object(self.manager, 'config', mock_cli_config_no_backend):

            # Call remove_schedule_keyword with existing keyword name
            self.manager.remove_schedule_keyword('sleep')

            # Confirm removed from manager config and file on disk
            self.assertNotIn('sleep', self.manager.config['schedule_keywords'])
            with open(mock_cli_config_path, 'r', encoding='utf-8') as file:
                config = json.load(file)
            self.assertNotIn('sleep', config['schedule_keywords'])

            # Confirm remove_schedule_keyword and save_schedule_keywords
            # endpoints were called once for each node
            self.assertEqual(mock_rm_keyword.call_count, 3)
            self.assertEqual(mock_save_keywords.call_count, 3)

            # Confirm no POST request was made
            mock_post.assert_not_called()

    def test_remove_schedule_keyword_backend_offline(self):
        # Confirm config contains sleep keyword
        self.assertIn('sleep', self.manager.config['schedule_keywords'])

        # Mock endpoints called by bulk API call functions
        # Mock _client.post to raise ConnectionError (simulate backend offline)
        # Mock print to confirm correct error was printed
        with patch('api_helper_functions.remove_schedule_keyword') as mock_rm_keyword, \
             patch('api_helper_functions.save_schedule_keywords') as mock_save_keywords, \
             patch.object(self.manager, '_client', MagicMock()) as mock_client, \
             patch.object(mock_client, 'post', side_effect=ConnectionError) as mock_post, \
             patch.object(self.manager, '_csrf_token', None), \
             patch('builtins.print') as mock_print:

            # Call remove_schedule_keyword with existing keyword name
            self.manager.remove_schedule_keyword('sleep')

            # Confirm removed from manager config and file on disk
            self.assertNotIn('sleep', self.manager.config['schedule_keywords'])
            with open(mock_cli_config_path, 'r', encoding='utf-8') as file:
                config = json.load(file)
            self.assertNotIn('sleep', config['schedule_keywords'])

            # Confirm remove_schedule_keyword and save_schedule_keywords
            # endpoints were called once for each node
            self.assertEqual(mock_rm_keyword.call_count, 3)
            self.assertEqual(mock_save_keywords.call_count, 3)

            # Confirm keyword was removed from django backend
            mock_post.assert_called_once_with(
                f'{self.manager.config["django_backend"]}/delete_schedule_keyword',
                json={
                    'keyword': 'sleep',
                    'sync_nodes': False
                },
                headers={
                    'X-CSRFToken': None
                },
                timeout=5
            )

            # Confirm correct error was printed
            mock_print.assert_called_with(
                'Failed to remove from django database (connection error)'
            )

    def test_load_config_file(self):
        # Call method with mock node name, confirm returns mock config file
        # created by mock_cli_config.json
        self.assertEqual(
            self.manager.load_node_config_file('Node1'),
            {'metadata': {'id': 'Node1'}}
        )

    def test_load_config_file_does_not_exist_no_django(self):
        # Create mock cli_config.json with no django backend configured
        mock_cli_config_no_backend = deepcopy(mock_cli_config)
        del mock_cli_config_no_backend['django_backend']

        # Mock os.path.exists to simulate file missing from disk
        # Mock cli_config.json to simulate no django backend
        with self.assertRaises(FileNotFoundError), \
             patch('os.path.exists', return_value=False), \
             patch.object(self.manager, 'config', mock_cli_config_no_backend):

            # Call method, should raise FileNotFoundError
            self.manager.load_node_config_file('Node1')

    def test_load_config_file_does_not_exist_django_configured(self):
        # Mock questionary.confirm.ask() to simulate user selecting no
        mock_confirm = MagicMock()
        mock_confirm.ask.return_value = False

        # Mock os.path.exists to simulate file missing from disk
        # Mock questionary.confirm to simulate user selecting no
        with self.assertRaises(FileNotFoundError), \
             patch('os.path.exists', return_value=False), \
             patch('questionary.confirm', return_value=mock_confirm):

            # Call method, should raise FileNotFoundError if user selects no
            self.manager.load_node_config_file('Node1')

        # Mock questionary.confirm.ask() to simulate user selecting yes
        mock_confirm.ask.return_value = True

        # Mock download_node_config_file_from_django method to confirm arguments
        # Mock save_node_config_file method to confirm arguments
        # Mock os.path.exists to simulate file missing from disk
        # Mock questionary.confirm to simulate user selecting yes
        with patch.object(self.manager, 'download_node_config_file_from_django') as mock_download, \
             patch.object(self.manager, 'save_node_config_file') as mock_save_config, \
             patch('os.path.exists', return_value=False), \
             patch('questionary.confirm', return_value=mock_confirm):

            # Mock download_node_config_file_from_django to return missing config
            mock_download.return_value = {'mock': 'config'}

            # Call method, should not raise exception
            self.manager.load_node_config_file('Node1')

            # Confirm download_node_config_file_from_django was called with
            # Node1 IP from cli_config.json
            mock_download.assert_called_once_with('192.168.1.123')

            # Confirm save_node_config_file was called with return value from
            # download_node_config_file_from_django
            mock_save_config.assert_called_once_with({'mock': 'config'})

    def test_load_config_file_does_not_exist_django_offline(self):
        # Mock questionary.confirm.ask() to simulate user selecting yes
        mock_confirm = MagicMock()
        mock_confirm.ask.return_value = True

        # Mock download_node_config_file_from_django method to return False (backend offline)
        # Mock save_node_config_file method to confirm not called
        # Mock os.path.exists to simulate file missing from disk
        # Mock questionary.confirm to simulate user selecting yes
        with patch.object(self.manager, 'download_node_config_file_from_django', return_value=False), \
             patch.object(self.manager, 'save_node_config_file') as mock_save_config, \
             patch('os.path.exists', return_value=False), \
             patch('questionary.confirm', return_value=mock_confirm):

            # Should raise FileNotFoundError when django connection fails
            with self.assertRaises(FileNotFoundError):
                self.manager.load_node_config_file('Node1')

            # Confirm did not write file to disk
            mock_save_config.assert_not_called()

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
             patch.object(mock_client, 'get', return_value=mock_response), \
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

    def test_download_node_config_file_from_django_backend_offline(self):
        # Mock _client.get to raise ConnectionError (simulate backend offline)
        # Mock _csrf_token to predictable value
        # Mock print to confirm correct error was printed
        with patch.object(self.manager, '_client', MagicMock()) as mock_client, \
             patch.object(mock_client, 'get', side_effect=ConnectionError) as mock_get, \
             patch.object(self.manager, '_csrf_token', None), \
             patch('builtins.print') as mock_print:

            # Call method with IP of existing node, confirm returns False
            self.assertFalse(
                self.manager.download_node_config_file_from_django('192.168.1.123')
            )

            # Confirm made correct GET request
            mock_get.assert_called_once_with(
                f'{self.manager.config["django_backend"]}/get_node_config/192.168.1.123',
                timeout=5
            )

            # Confirm correct error was printed
            mock_print.assert_called_with(
                'Failed to download config from django database (connection error)'
            )

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
            expected_calls = [
                call('192.168.1.123'),
                call('192.168.1.234'),
                call('192.168.1.111'),
            ]
            self.assertCountEqual(mock_download.call_args_list, expected_calls)

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
        with open(mock_cli_config_path, 'r', encoding='utf-8') as file:
            config = json.load(file)
        self.assertEqual(config['django_backend'], 'http://10.0.0.1:9999')

        # Simulate no open connection
        self.manager._client = None

        # Call method again to change back
        self.manager.set_django_address('http://192.168.1.100')

        # Confirm changed back in class attribute and on disk
        self.assertEqual(
            self.manager.config['django_backend'],
            'http://192.168.1.100'
        )
        with open(mock_cli_config_path, 'r', encoding='utf-8') as file:
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
        with open(mock_cli_config_path, 'r', encoding='utf-8') as file:
            config = json.load(file)
        self.assertEqual(config['config_directory'], '/fake/config/path')

        # Call method again to change back
        self.manager.set_config_directory(mock_config_dir)

        # Confirm changed back in class attribute and on disk
        self.assertEqual(
            self.manager.config['config_directory'],
            mock_config_dir
        )
        with open(mock_cli_config_path, 'r', encoding='utf-8') as file:
            config = json.load(file)
        self.assertEqual(config['config_directory'], mock_config_dir)

    def test_set_webrepl_password(self):
        # Call method to change password
        self.manager.set_webrepl_password('newpass')

        # Confirm changed in class attribute and on disk
        self.assertEqual(self.manager.config['webrepl_password'], 'newpass')
        with open(mock_cli_config_path, 'r', encoding='utf-8') as file:
            config = json.load(file)
        self.assertEqual(config['webrepl_password'], 'newpass')

        # Call method again to change back
        self.manager.set_webrepl_password('password')

        # Confirm changed back in class attribute and on disk
        self.assertEqual(self.manager.config['webrepl_password'], 'password')
        with open(mock_cli_config_path, 'r', encoding='utf-8') as file:
            config = json.load(file)
        self.assertEqual(config['webrepl_password'], 'password')


class TestInstantiation(TestCase):
    '''Tests CliConfigManager singleton initial instantiation'''

    def setUp(self):
        # Mock path to cli_config.json (prevent overwriting real file)
        self.cli_config_patch = patch(
            'cli_config_manager.get_cli_config_path',
            return_value=mock_cli_config_path
        )
        self.cli_config_patch.start()

    def tearDown(self):
        self.cli_config_patch.stop()

        # Overwrite mock_cli_config with original contents
        with open(mock_cli_config_path, 'w', encoding='utf-8') as file:
            json.dump(mock_cli_config, file)

    def test_instantiate_with_django_backend(self):
        # Create mock to replace CliConfigManager._client
        mock_client = MagicMock()

        # Create mock /get_cli_config endpoint response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'status': 'success',
            'message': {
                'nodes': {
                    'node1': '192.168.1.123',
                    'node2': '192.168.1.234',
                    'node3': '192.168.1.111'
                },
                'schedule_keywords': {
                    'sunrise': '06:00',
                    'sunset': '18:00',
                    'sleep': '22:00'
                }
            }
        }

        # Mock requests.session to return mock_client
        # Mock _client.get to confirm correct request made
        # Mock _client.get return value to simulate actual response
        # Mock attributes to trick singleton into creating new instance
        with patch('cli_config_manager.requests.session', return_value=mock_client), \
             patch.object(mock_client, 'get') as mock_get, \
             patch.object(mock_get, 'get', return_value=mock_response), \
             patch.object(CliConfigManager, '_instance', None), \
             patch.object(CliConfigManager, '_initialized', False):

            # Instantiate class (should create new instance due to mocks)
            manager = CliConfigManager()

            # Confirm singleton attributes were set to prevent creating duplicate
            self.assertTrue(manager._initialized)
            self.assertIsNotNone(manager._instance)

            # Confirm config attribute contains config file read from disk
            self.assertEqual(manager.config, mock_cli_config)

            # Confirm _client was created, correct GET request was made
            self.assertIsNotNone(manager._client)
            self.assertEqual(manager._client, mock_client)
            mock_get.assert_called_once_with(
                f'{mock_cli_config["django_backend"]}/get_cli_config',
                timeout=5
            )

    def test_instantiate_without_django_backend(self):
        # Create mock cli_config.json with no django backend configured
        mock_cli_config_no_backend = deepcopy(mock_cli_config)
        del mock_cli_config_no_backend['django_backend']

        # Create mock to replace CliConfigManager._client
        mock_client = MagicMock()

        # Mock requests.session to return mock_client
        # Mock _client.get to confirm no request made
        # Mock attributes to trick singleton into creating new instance
        # Mock cli_config.json to simulate no django backend
        with patch('cli_config_manager.requests.session', return_value=mock_client), \
             patch.object(mock_client, 'get') as mock_get, \
             patch.object(CliConfigManager, '_instance', None), \
             patch.object(CliConfigManager, '_initialized', False), \
             patch('cli_config_manager.json.load', return_value=mock_cli_config_no_backend):

            # Instantiate class (should create new instance due to mocks)
            manager = CliConfigManager()

            # Confirm singleton attributes were set to prevent creating duplicate
            self.assertTrue(manager._initialized)
            self.assertIsNotNone(manager._instance)

            # Confirm config attribute contains config file read from disk
            self.assertEqual(manager.config, mock_cli_config_no_backend)

            # Confirm did NOT create client, did NOT make GET request
            self.assertIsNone(manager._client)
            mock_get.assert_not_called()

    def test_instantiate_with_django_backend_ignore_ssl_errors(self):
        # Create mock cli_config.json with ignore_ssl_errors set to true
        mock_cli_config_ignore_ssl = deepcopy(mock_cli_config)
        mock_cli_config_ignore_ssl['ignore_ssl_errors'] = True

        # Create mock to replace CliConfigManager._client
        mock_client = MagicMock()

        # Create mock /get_cli_config endpoint response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'status': 'success',
            'message': {
                'nodes': {
                    'node1': '192.168.1.123',
                    'node2': '192.168.1.234',
                    'node3': '192.168.1.111'
                },
                'schedule_keywords': {
                    'sunrise': '06:00',
                    'sunset': '18:00',
                    'sleep': '22:00'
                }
            }
        }

        # Mock requests.session to return mock_client
        # Mock _client.get to confirm correct request made
        # Mock _client.get return value to simulate actual response
        # Mock attributes to trick singleton into creating new instance
        # Mock cli_config.json to simulate ignore_ssl_errors setting
        with patch('cli_config_manager.requests.session', return_value=mock_client), \
             patch.object(mock_client, 'get') as mock_get, \
             patch.object(mock_get, 'get', return_value=mock_response), \
             patch.object(CliConfigManager, '_instance', None), \
             patch.object(CliConfigManager, '_initialized', False), \
             patch('cli_config_manager.json.load', return_value=mock_cli_config_ignore_ssl):

            # Instantiate class (should create new instance due to mocks)
            manager = CliConfigManager()

            # Confirm singleton attributes were set to prevent creating duplicate
            self.assertTrue(manager._initialized)
            self.assertIsNotNone(manager._instance)

            # Confirm config attribute contains config file read from disk
            self.assertEqual(manager.config, mock_cli_config_ignore_ssl)

            # Confirm _client was created, correct GET request was made
            self.assertIsNotNone(manager._client)
            self.assertEqual(manager._client, mock_client)
            mock_get.assert_called_once_with(
                f'{mock_cli_config["django_backend"]}/get_cli_config',
                timeout=5
            )

            # Confirm _client.verify is set to False
            self.assertFalse(manager._client.verify)


class TestRegressions(TestCase):
    def setUp(self):
        # Mock path to cli_config.json (prevent overwriting real file)
        self.cli_config_patch = patch(
            'cli_config_manager.get_cli_config_path',
            return_value=mock_cli_config_path
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

    def test_crashes_after_changing_django_address(self):
        '''Original bug: CliConfigManager._client retained cookies from the old
        django backend when address was changed. The next time sync_from_django
        was called (adds second csrftoken cookie with new domain) an uncaught
        exception occurred when trying to save cookie to _csrf_token attribute
        (CookieConflictError: There are multiple cookies with name, 'csrftoken').

        The set_django_address method now clears existing cookies.
        '''

        # Replace _client with empty session (not mock, methods will be mocked)
        self.manager._client = requests.Session()

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

        # Add a mock csrftoken cookie that will be saved by self.manager
        mock_response.cookies = requests.cookies.RequestsCookieJar()
        mock_response.cookies.set('csrftoken', 'fBMfx', domain='old.address.com')

        # Create mock requests.Session.get that returns the mock response and
        # manually adds the mock cookie to _client.cookies
        def mock_get(url, *args, **kwargs):
            self.manager._client.cookies.update(mock_response.cookies)
            return mock_response

        # Mock _client.get to return mock response object and set mock cookie
        with patch.object(self.manager._client, 'get', side_effect=mock_get), \
             patch.object(self.manager, 'write_cli_config_to_disk'):

            # Call sync method
            self.manager.sync_from_django()

            # Confirm the csrftoken cookie was saved
            self.assertEqual(self.manager._csrf_token, 'fBMfx')

        # Change django address (after fix this should clear all session cookies)
        with patch.object(self.manager, 'write_cli_config_to_disk'):
            self.manager.set_django_address('http://new.address.com')

            # Confirm existing cookies were cleared
            self.assertFalse(self.manager._client.cookies)

        # Replace the mock csrftoken value and domain (simulate new backend)
        mock_response.cookies.clear(domain='old.address.com', path='/', name='csrftoken')
        mock_response.cookies.set('csrftoken', 'KTmdv', domain='new.address.com')

        # Mock _client.get to return mock response object and set mock cookie
        with patch.object(self.manager._client, 'get', side_effect=mock_get), \
             patch.object(self.manager, 'write_cli_config_to_disk'):

            # Call sync method, should not crash due to duplicate CSRF token
            self.manager.sync_from_django()

            # Confirm the new csrftoken cookie was saved
            self.assertEqual(self.manager._csrf_token, 'KTmdv')
