import os
from unittest import TestCase
from unittest.mock import patch, MagicMock, mock_open
from smarthome_cli import (
    main_prompt,
    manage_nodes_prompt,
    edit_node_config_prompt,
    create_new_node_prompt,
    upload_config_from_disk,
    view_log_prompt,
    change_node_ip_prompt,
    delete_prompt,
    sync_prompt
)
from mock_cli_config import mock_cli_config


class TestMainPrompt(TestCase):
    '''Tests the main menu prompt, confirms options call correct function'''

    def setUp(self):
        # Mock replaces .ask() method to simulate user input
        self.mock_ask = MagicMock()

    def test_api_prompt(self):
        # Mock user selecting "API client", then "Done" (exit main menu loop)
        self.mock_ask.unsafe_ask.side_effect = ['API client', 'Done']

        with patch('questionary.select', return_value=self.mock_ask), \
             patch('smarthome_cli.api_prompt') as mock_api_prompt:

            # Run prompt, will complete immediately with mock input
            main_prompt()

            # Confirm api_prompt was called
            mock_api_prompt.assert_called_once()

    def test_manage_nodes_prompt(self):
        # Mock user selecting "Manage nodes", then "Done" (exit main menu loop)
        self.mock_ask.unsafe_ask.side_effect = ['Manage nodes', 'Done']

        with patch('questionary.select', return_value=self.mock_ask), \
             patch('smarthome_cli.manage_nodes_prompt') as mock_manage_nodes_prompt:

            # Run prompt, will complete immediately with mock input
            main_prompt()

            # Confirm manage_nodes_prompt was called
            mock_manage_nodes_prompt.assert_called_once()

    def test_sync_prompt(self):
        # Mock user selecting "Settings", then "Done" (exit main menu loop)
        self.mock_ask.unsafe_ask.side_effect = ['Settings', 'Done']

        with patch('questionary.select', return_value=self.mock_ask), \
             patch('smarthome_cli.sync_prompt') as mock_sync_prompt:

            # Run prompt, will complete immediately with mock input
            main_prompt()

            # Confirm sync_prompt was called
            mock_sync_prompt.assert_called_once()


class TestManageNodesPrompt(TestCase):
    '''Tests the manage nodes prompt, confirms options call correct function'''

    def setUp(self):
        # Mock replaces .ask() method to simulate user input
        self.mock_ask = MagicMock()

    def test_create_new_node(self):
        # Mock user selecting "Create new node", then "Done" (exit loop)
        self.mock_ask.unsafe_ask.side_effect = ['Create new node', 'Done']

        with patch('questionary.select', return_value=self.mock_ask), \
             patch('smarthome_cli.create_new_node_prompt') as mock_new_node_prompt:

            # Run prompt, will complete immediately with mock input
            manage_nodes_prompt()

            # Confirm create_new_node_prompt was called
            mock_new_node_prompt.assert_called_once()

    def test_edit_existing_node_config(self):
        # Mock user selecting "Edit existing node config", then "Done" (exit loop)
        self.mock_ask.unsafe_ask.side_effect = [
            'Edit existing node config',
            'Done'
        ]

        with patch('questionary.select', return_value=self.mock_ask), \
             patch('smarthome_cli.edit_node_config_prompt') as mock_edit_node_prompt:

            # Run prompt, will complete immediately with mock input
            manage_nodes_prompt()

            # Confirm edit_node_config_prompt was called
            mock_edit_node_prompt.assert_called_once()

    def test_reupload_config_to_node(self):
        # Mock user selecting "Reupload config to node", then node name from
        # mock_cli_config, then "Done" (exit loop)
        self.mock_ask.unsafe_ask.side_effect = [
            'Reupload config to node',
            'node1',
            'Done'
        ]

        with patch('questionary.select', return_value=self.mock_ask), \
             patch('smarthome_cli.upload_node') as mock_upload_node:

            # Run prompt, will complete immediately with mock input
            manage_nodes_prompt()

            # Confirm upload_node was called with selected node + mock password
            mock_upload_node.assert_called_once_with('node1', 'password')

    def test_upload_config_file_from_disk(self):
        # Mock user selecting "Upload config file from disk", then "Done" (exit loop)
        self.mock_ask.unsafe_ask.side_effect = [
            'Upload config file from disk',
            'Done'
        ]

        with patch('questionary.select', return_value=self.mock_ask), \
             patch('smarthome_cli.upload_config_from_disk') as mock_upload_config:

            # Run prompt, will complete immediately with mock input
            manage_nodes_prompt()

            # Confirm upload_config_from_disk prompt was called
            mock_upload_config.assert_called_once()

    def test_change_existing_node_ip(self):
        # Mock user selecting "Change existing node IP", then "Done" (exit loop)
        self.mock_ask.unsafe_ask.side_effect = [
            'Change existing node IP',
            'Done'
        ]

        with patch('questionary.select', return_value=self.mock_ask), \
             patch('smarthome_cli.change_node_ip_prompt') as mock_change_ip_prompt:

            # Run prompt, will complete immediately with mock input
            manage_nodes_prompt()

            # Confirm change_node_ip_prompt was called
            mock_change_ip_prompt.assert_called_once()

    def test_delete_existing_node(self):
        # Mock user selecting "Delete existing node", then "Done" (exit loop)
        self.mock_ask.unsafe_ask.side_effect = [
            'Delete existing node',
            'Done'
        ]

        with patch('questionary.select', return_value=self.mock_ask), \
             patch('smarthome_cli.delete_prompt') as mock_delete_prompt:

            # Run prompt, will complete immediately with mock input
            manage_nodes_prompt()

            # Confirm delete_prompt was called with selected node + mock password
            mock_delete_prompt.assert_called_once()

    def test_view_node_log(self):
        # Mock user selecting "View node log", then "Done" (exit loop)
        self.mock_ask.unsafe_ask.side_effect = [
            'View node log',
            'Done'
        ]

        with patch('questionary.select', return_value=self.mock_ask), \
             patch('smarthome_cli.view_log_prompt') as mock_view_log_prompt:

            # Run prompt, will complete immediately with mock input
            manage_nodes_prompt()

            # Confirm view_log_prompt was called with selected node + mock password
            mock_view_log_prompt.assert_called_once()


class TestSettingsPrompt(TestCase):
    '''Tests the settings prompt, confirms options call correct function'''

    def setUp(self):
        # Mock replaces .ask() method to simulate user input
        self.mock_ask = MagicMock()

    def test_set_django_address(self):
        # Mock user selecting "View node log", entering django server address,
        # then selecting "Done" (exit loop)
        self.mock_ask.unsafe_ask.side_effect = [
            'Set django address',
            'http://192.168.1.100:8123',
            'Done'
        ]

        with patch('questionary.select', return_value=self.mock_ask), \
             patch('questionary.text', return_value=self.mock_ask), \
             patch('smarthome_cli.cli_config.set_django_address') as mock_set_address:

            # Run prompt, will complete immediately with mock input
            sync_prompt()

            # Confirm cli_config.set_django_address was called with user input
            mock_set_address.assert_called_once_with('http://192.168.1.100:8123')

    def test_sync_nodes_and_keywords_from_django(self):
        # Mock user selecting "Sync nodes and keywords from django", then
        # selecting "Done" (exit loop)
        self.mock_ask.unsafe_ask.side_effect = [
            'Sync nodes and keywords from django',
            'Done'
        ]

        with patch('questionary.select', return_value=self.mock_ask), \
             patch('smarthome_cli.cli_config.sync_from_django') as mock_sync:

            # Run prompt, will complete immediately with mock input
            sync_prompt()

            # Confirm cli_config.sync_from_django was called
            mock_sync.assert_called_once()

    def test_download_all_config_files_from_django(self):
        # Mock user selecting "Download all config files from django", then
        # selecting "Done" (exit loop)
        self.mock_ask.unsafe_ask.side_effect = [
            'Download all config files from django',
            'Done'
        ]

        with patch('questionary.select', return_value=self.mock_ask), \
             patch('smarthome_cli.cli_config.download_all_node_config_files_from_django') as mock_download:

            # Run prompt, will complete immediately with mock input
            sync_prompt()

            # Confirm cli_config.download_all_node_config_files_from_django was called
            mock_download.assert_called_once()

    def test_change_config_directory(self):
        # Mock user selecting "View node log", entering config directory path,
        # then selecting "Done" (exit loop)
        self.mock_ask.unsafe_ask.side_effect = [
            'Change config directory',
            '/home/user/git/micropython-smarthome/config_files',
            'Done'
        ]

        with patch('questionary.select', return_value=self.mock_ask), \
             patch('questionary.text', return_value=self.mock_ask), \
             patch('smarthome_cli.cli_config.set_config_directory') as mock_set_dir:

            # Run prompt, will complete immediately with mock input
            sync_prompt()

            # Confirm cli_config.set_config_directory was called with user input
            mock_set_dir.assert_called_once_with(
                '/home/user/git/micropython-smarthome/config_files'
            )

    def test_change_webrepl_password(self):
        # Mock user selecting "View node log", entering webrepl password, then
        # selecting "Done" (exit loop)
        self.mock_ask.unsafe_ask.side_effect = [
            'Change webrepl password',
            'password',
            'Done'
        ]

        with patch('questionary.select', return_value=self.mock_ask), \
             patch('questionary.text', return_value=self.mock_ask), \
             patch('smarthome_cli.cli_config.set_webrepl_password') as mock_set_password:

            # Run prompt, will complete immediately with mock input
            sync_prompt()

            # Confirm cli_config.set_webrepl_password was called with user input
            mock_set_password.assert_called_once_with('password')


class TestManageNodeFunctions(TestCase):
    '''Tests the functions called by manage nodes prompt options'''

    def setUp(self):
        # Mock replaces .ask() method to simulate user input
        self.mock_ask = MagicMock()

    def test_create_new_node_prompt(self):
        # Create mock GenerateConfigFile instance to confirm methods were called
        mock_generator = MagicMock()
        mock_generator.run_prompt = MagicMock()
        mock_generator.passed_validation = True
        mock_generator.write_to_disk = MagicMock()
        mock_generator.config = {'metadata': {'id': 'mock_name'}}

        # Mock GenerateConfigFile class to return mock instance
        # Mock helper functions called after user completes config prompts
        with patch('smarthome_cli.GenerateConfigFile', return_value=mock_generator) as mock_generator_class, \
             patch('smarthome_cli.get_config_filename', return_value='mock.json') as mock_get_filename, \
             patch('smarthome_cli.upload_config_from_disk') as mock_upload_config, \
             patch('questionary.confirm', MagicMock()) as mock_confirm:

            # Answer "Yes" to "Upload config to ESP32?" prompt
            mock_confirm.return_value.unsafe_ask.return_value = True

            # Call function
            create_new_node_prompt()

            # Confirm GenerateConfigFile was instantiated
            mock_generator_class.assert_called_once()

            # Confirm prompt was shown, config was written to disk
            mock_generator.run_prompt.assert_called_once()
            mock_generator.write_to_disk.assert_called_once()

            # Confirm requested filename for new config
            mock_get_filename.assert_called_once()

            # Confirm called upload prompt with filename as arg
            mock_upload_config.assert_called_once_with('mock.json')

    def test_edit_existing_node_config(self):
        # Mock user selecting name of existing node
        self.mock_ask.unsafe_ask.return_value = 'node1'

        # Create mock GenerateConfigFile instance to confirm methods were called
        mock_generator = MagicMock()
        mock_generator.run_prompt = MagicMock()
        mock_generator.passed_validation = True
        mock_generator.write_to_disk = MagicMock()
        mock_generator.config = {'metadata': {'id': 'Node1'}}

        # Mock select prompt to return mocked node selection
        # Mock GenerateConfigFile class to return mock instance
        # Mock helper functions called after user completes config prompts
        with patch('questionary.select', return_value=self.mock_ask), \
             patch('smarthome_cli.GenerateConfigFile', return_value=mock_generator) as mock_generator_class, \
             patch('smarthome_cli.cli_config.get_config_filepath', return_value='node1.json') as mock_get_path, \
             patch('smarthome_cli.upload_node') as mock_upload_node, \
             patch('questionary.confirm', MagicMock()) as mock_confirm:

            # Answer "Yes" to "Reupload now?" prompt
            mock_confirm.return_value.ask.return_value = True

            # Call function
            edit_node_config_prompt()

            # Confirm requested path to selected node config file
            mock_get_path.assert_called_once_with('node1')

            # Confirm GenerateConfigFile was instantiated with path to config file
            mock_generator_class.assert_called_once_with('node1.json')

            # Confirm prompt was shown, config was written to disk
            mock_generator.run_prompt.assert_called_once()
            mock_generator.write_to_disk.assert_called_once()

            # Confirm called upload_node with node name and webrepl password
            mock_upload_node.assert_called_once_with('node1', 'password')

    def test_upload_config_from_disk(self):
        # Mock user entering IP address, then selecting existing config file
        self.mock_ask.unsafe_ask.side_effect = [
            '192.168.1.123',
            'node2.json'
        ]

        with patch('questionary.select', return_value=self.mock_ask), \
             patch('questionary.text', return_value=self.mock_ask), \
             patch('smarthome_cli.upload_config_to_ip') as mock_upload_config:

            # Call prompt with no argument
            upload_config_from_disk()

            # Confirm called upload_config_to_ip with user-entered IP, absolute
            # path to selected config file
            mock_upload_config.assert_called_once_with(
                config_path=os.path.join(
                    mock_cli_config['config_directory'], 'node2.json'
                ),
                ip='192.168.1.123',
                webrepl_password='password'
            )

    def test_view_log_prompt(self):
        # Mock user selecting name of existing node, then enter filename to save log
        self.mock_ask.unsafe_ask.side_effect = [
            'node1',
            'node_log.txt'
        ]

        # Create mock Webrepl instance to confirm methods were called
        mock_connection = MagicMock()
        mock_connection.get_file_mem = MagicMock(return_value=b'mock_log')

        # Mock select prompt to return mocked node selection
        # Mock text prompt to return mocked log filename
        # Mock Webrepl class to return mock instance
        # Mock pydoc.pager (called to display log)
        with patch('questionary.select', return_value=self.mock_ask), \
             patch('questionary.text', return_value=self.mock_ask), \
             patch('smarthome_cli.Webrepl', return_value=mock_connection) as mock_webrepl_class, \
             patch('smarthome_cli.pydoc.pager') as mock_pager, \
             patch('questionary.confirm', MagicMock()) as mock_confirm, \
             patch("builtins.open", mock_open()) as mocked_open:

            # Answer "Yes" to "Save log?" prompt
            mock_confirm.return_value.ask.return_value = True

            # Call function
            view_log_prompt()

            # Confirm Webrepl was instantiated with selected node IP + webrepl password
            mock_webrepl_class.assert_called_once_with('192.168.1.123', 'password')

            # Confirm get_file_mem was called with name of log file
            mock_connection.get_file_mem.assert_called_once_with('app.log')

            # Confirm pager was called with decoded log
            mock_pager.assert_called_once_with('mock_log')

            # Confirm opened 'node_log.text' and wrote mock log contents to disk
            mocked_open.assert_called_once_with('node_log.txt', 'w', encoding='utf-8')
            mock_file = mocked_open()
            mock_file.write.assert_called_once_with('mock_log')

    def test_change_node_ip_prompt(self):
        # Mock user selecting node name then entering new IP address
        self.mock_ask.unsafe_ask.side_effect = [
            'node1',
            '192.168.1.222'
        ]

        # Mock select and text prompts to return mocked user input
        # Mock cli_config.change_node_ip to confirm called with user input
        with patch('questionary.select', return_value=self.mock_ask), \
             patch('questionary.text', return_value=self.mock_ask), \
             patch('smarthome_cli.cli_config.change_node_ip') as mock_change_ip:

            # Run prompt, will complete immediately with mock input
            change_node_ip_prompt()

            # Confirm cli_config.change_node_ip was called with correct args
            mock_change_ip.assert_called_once_with('node1', '192.168.1.222')

    def test_delete_prompt(self):
        # Mock user checking 2 nodes at checkbox prompt, then selecting "Yes"
        # at confirmation prompt
        self.mock_ask.unsafe_ask.side_effect = [
            ['node1', 'node3'],
            'Yes'
        ]

        # Mock checkbox and select prompts to return mocked user input
        # Mock cli_config.remove_node to confirm called with selected node names
        with patch('questionary.select', return_value=self.mock_ask), \
             patch('questionary.checkbox', return_value=self.mock_ask), \
             patch('smarthome_cli.cli_config.remove_node') as mock_remove_node:

            # Run prompt, will complete immediately with mock input
            delete_prompt()

            # Confirm cli_config.remove_node was called with both selected nodes
            self.assertEqual(len(mock_remove_node.call_args_list), 2)
            self.assertEqual(mock_remove_node.call_args_list[0][0][0], 'node1')
            self.assertEqual(mock_remove_node.call_args_list[1][0][0], 'node3')
