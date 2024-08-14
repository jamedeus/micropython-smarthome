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
        self.assertNotIn('new', self.manager.config['nodes'])

        # Confim with expected name does not exist in config_directory
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
            with open(mock_cli_config_path, 'r') as file:
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

        # Confim mock config was written to config_directory
        self.assertTrue(os.path.exists(os.path.join(mock_config_dir, 'new.json')))

    def test_add_node_no_backend_configured(self):
        # Confirm config object does not contain name that will be added
        self.assertNotIn('new', self.manager.config['nodes'])

        # Confim with expected name does not exist in config_directory
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
            with open(mock_cli_config_path, 'r') as file:
                config = json.load(file)
            self.assertIn('new', config['nodes'])

            # Confirm no POST request was made
            mock_post.assert_not_called()

        # Confim mock config was written to config_directory
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
            with open(mock_cli_config_path, 'r') as file:
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

    def test_remove_node_backend_offline(self):
        # Confirm config object contains node3
        self.assertIn('node3', self.manager.config['nodes'])

        # Mock _client.post to confirm not called
        # Mock os.path.exists to return False (config missing from disk)
        with patch.object(self.manager, '_client', MagicMock()) as mock_client, \
             patch.object(mock_client, 'post', side_effect=OSError) as mock_post, \
             patch.object(self.manager, '_csrf_token', None), \
             patch('builtins.print') as mock_print:

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
            with open(mock_cli_config_path, 'r') as file:
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
            with open(mock_cli_config_path, 'r') as file:
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
            with open(mock_cli_config_path, 'r') as file:
                config = json.load(file)
            self.assertEqual(config['nodes']['node3'], '192.168.1.222')

            # Confirm django error was printed
            mock_print.assert_called_with('New IP must be different than old')

    def test_add_schedule_keyword(self):
        # Confirm config does not contain NewName keyword
        self.assertNotIn('NewName', self.manager.config['schedule_keywords'])

        # Create mock django response object
        mock_response = MagicMock()
        mock_response.status_code = 200

        # Mock bulk API call functions called by method
        # Mock _client.post to confirm correct request made to django backend
        with patch('cli_config_manager.bulk_add_schedule_keyword') as mock_add_keyword, \
             patch('cli_config_manager.bulk_save_schedule_keyword') as mock_save_keywords, \
             patch.object(self.manager, '_client', MagicMock()) as mock_client, \
             patch.object(mock_client, 'post', return_value=mock_response) as mock_post, \
             patch.object(self.manager, '_csrf_token', None):

            # Call add_schedule_keyword with new keyword name and timestamp
            self.manager.add_schedule_keyword('NewName', '12:34')

            # Confirm added to manager config and file on disk
            self.assertIn('NewName', self.manager.config['schedule_keywords'])
            self.assertEqual(self.manager.config['schedule_keywords']['NewName'], '12:34')
            with open(mock_cli_config_path, 'r') as file:
                config = json.load(file)
            self.assertIn('NewName', config['schedule_keywords'])
            self.assertEqual(config['schedule_keywords']['NewName'], '12:34')

            # Confirm bulk API call functions were called with expected args
            mock_add_keyword.assert_called_once_with(
                ['192.168.1.123', '192.168.1.234', '192.168.1.111'],
                'NewName',
                '12:34'
            )
            mock_save_keywords.assert_called_once_with(
                ['192.168.1.123', '192.168.1.234', '192.168.1.111']
            )

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

        # Mock bulk API call functions called by method
        # Mock _client.post to confirm no request made
        # Mock cli_config.json to simulate no django backend
        with patch('cli_config_manager.bulk_add_schedule_keyword') as mock_add_keyword, \
             patch('cli_config_manager.bulk_save_schedule_keyword') as mock_save_keywords, \
             patch.object(self.manager, '_client', MagicMock()) as mock_client, \
             patch.object(mock_client, 'post') as mock_post, \
             patch.object(self.manager, 'config', mock_cli_config_no_backend):

            # Call add_schedule_keyword with new keyword name and timestamp
            self.manager.add_schedule_keyword('NewName', '12:34')

            # Confirm added to manager config and file on disk
            self.assertIn('NewName', self.manager.config['schedule_keywords'])
            self.assertEqual(self.manager.config['schedule_keywords']['NewName'], '12:34')
            with open(mock_cli_config_path, 'r') as file:
                config = json.load(file)
            self.assertIn('NewName', config['schedule_keywords'])
            self.assertEqual(config['schedule_keywords']['NewName'], '12:34')

            # Confirm bulk API call functions were called with expected args
            mock_add_keyword.assert_called_once_with(
                ['192.168.1.123', '192.168.1.234', '192.168.1.111'],
                'NewName',
                '12:34'
            )
            mock_save_keywords.assert_called_once_with(
                ['192.168.1.123', '192.168.1.234', '192.168.1.111']
            )

            # Confirm no POST request was made
            mock_post.assert_not_called()

    def test_edit_schedule_keyword(self):
        # Confirm config contains sleep keyword, does not contain NewName
        self.assertIn('sleep', self.manager.config['schedule_keywords'])
        self.assertNotIn('NewName', self.manager.config['schedule_keywords'])

        # Create mock django response object
        mock_response = MagicMock()
        mock_response.status_code = 200

        # Mock bulk API call functions called by method
        # Mock _client.post to confirm correct request made to django backend
        with patch('cli_config_manager.bulk_edit_schedule_keyword') as mock_edit_keyword, \
             patch('cli_config_manager.bulk_save_schedule_keyword') as mock_save_keywords, \
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
            with open(mock_cli_config_path, 'r') as file:
                config = json.load(file)
            self.assertNotIn('sleep', config['schedule_keywords'])
            self.assertIn('NewName', config['schedule_keywords'])
            self.assertEqual(config['schedule_keywords']['NewName'], '12:34')

            # Confirm bulk API call functions were called with expected args
            mock_edit_keyword.assert_called_once_with(
                ['192.168.1.123', '192.168.1.234', '192.168.1.111'],
                'sleep',
                'NewName',
                '12:34'
            )
            mock_save_keywords.assert_called_once_with(
                ['192.168.1.123', '192.168.1.234', '192.168.1.111']
            )

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

    def test_edit_schedule_keyword_no_django(self):
        # Confirm config contains sleep keyword, does not contain NewName
        self.assertIn('sleep', self.manager.config['schedule_keywords'])
        self.assertNotIn('NewName', self.manager.config['schedule_keywords'])

        # Create mock cli_config.json with no django backend configured
        mock_cli_config_no_backend = deepcopy(mock_cli_config)
        del mock_cli_config_no_backend['django_backend']

        # Mock bulk API call functions called by method
        # Mock _client.post to confirm correct request made to django backend
        with patch('cli_config_manager.bulk_edit_schedule_keyword') as mock_edit_keyword, \
             patch('cli_config_manager.bulk_save_schedule_keyword') as mock_save_keywords, \
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
            with open(mock_cli_config_path, 'r') as file:
                config = json.load(file)
            self.assertNotIn('sleep', config['schedule_keywords'])
            self.assertIn('NewName', config['schedule_keywords'])
            self.assertEqual(config['schedule_keywords']['NewName'], '12:34')

            # Confirm bulk API call functions were called with expected args
            mock_edit_keyword.assert_called_once_with(
                ['192.168.1.123', '192.168.1.234', '192.168.1.111'],
                'sleep',
                'NewName',
                '12:34'
            )
            mock_save_keywords.assert_called_once_with(
                ['192.168.1.123', '192.168.1.234', '192.168.1.111']
            )

            # Confirm no POST request was made
            mock_post.assert_not_called()

    def test_remove_schedule_keyword(self):
        # Confirm config contains sleep keyword
        self.assertIn('sleep', self.manager.config['schedule_keywords'])

        # Create mock django response object
        mock_response = MagicMock()
        mock_response.status_code = 200

        # Mock bulk API call functions called by method
        with patch('cli_config_manager.bulk_remove_schedule_keyword') as mock_rm_keyword, \
             patch('cli_config_manager.bulk_save_schedule_keyword') as mock_save_keywords, \
             patch.object(self.manager, '_client', MagicMock()) as mock_client, \
             patch.object(mock_client, 'post', return_value=mock_response) as mock_post, \
             patch.object(self.manager, '_csrf_token', None):

            # Call remove_schedule_keyword with existing keyword name
            self.manager.remove_schedule_keyword('sleep')

            # Confirm added to manager config and file on disk
            self.assertNotIn('sleep', self.manager.config['schedule_keywords'])
            with open(mock_cli_config_path, 'r') as file:
                config = json.load(file)
            self.assertNotIn('sleep', config['schedule_keywords'])

            # Confirm bulk API call functions were called with expected args
            mock_rm_keyword.assert_called_once_with(
                ['192.168.1.123', '192.168.1.234', '192.168.1.111'],
                'sleep'
            )
            mock_save_keywords.assert_called_once_with(
                ['192.168.1.123', '192.168.1.234', '192.168.1.111']
            )

            # Confirm keyword was removeed from django backend
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

        # Mock bulk API call functions called by method
        # Mock _client.post to confirm correct request made to django backend
        with patch('cli_config_manager.bulk_remove_schedule_keyword') as mock_rm_keyword, \
             patch('cli_config_manager.bulk_save_schedule_keyword') as mock_save_keywords, \
             patch.object(self.manager, '_client', MagicMock()) as mock_client, \
             patch.object(mock_client, 'post') as mock_post, \
             patch.object(self.manager, 'config', mock_cli_config_no_backend):

            # Call remove_schedule_keyword with existing keyword name
            self.manager.remove_schedule_keyword('sleep')

            # Confirm added to manager config and file on disk
            self.assertNotIn('sleep', self.manager.config['schedule_keywords'])
            with open(mock_cli_config_path, 'r') as file:
                config = json.load(file)
            self.assertNotIn('sleep', config['schedule_keywords'])

            # Confirm bulk API call functions were called with expected args
            mock_rm_keyword.assert_called_once_with(
                ['192.168.1.123', '192.168.1.234', '192.168.1.111'],
                'sleep'
            )
            mock_save_keywords.assert_called_once_with(
                ['192.168.1.123', '192.168.1.234', '192.168.1.111']
            )

            # Confirm no POST request was made
            mock_post.assert_not_called()

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
