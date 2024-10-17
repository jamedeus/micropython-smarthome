# pylint: disable=line-too-long, missing-function-docstring, missing-module-docstring, missing-class-docstring

import os
from copy import deepcopy
from unittest import TestCase
from unittest.mock import patch, MagicMock, mock_open
from smarthome_cli import (
    main,
    main_prompt,
    setup_prompt,
    manage_nodes_prompt,
    edit_node_config_prompt,
    create_new_node_prompt,
    upload_config_from_disk,
    view_log_prompt,
    change_node_ip_prompt,
    delete_node_prompt,
    manage_keywords_prompt,
    settings_prompt
)
from mock_cli_config import mock_cli_config, mock_cli_config_path


class TestCommandLineArguments(TestCase):
    '''Tests command line argument handling'''

    def test_no_arg(self):
        # Mock empty sys.argv (should show main prompt)
        with patch('sys.argv', ['smarthome_cli']), \
             patch('smarthome_cli.main_prompt') as mock_main_prompt:

            # Simulate calling from command line, confirm shows main prompt
            main()
            mock_main_prompt.assert_called_once()

        # Mock --no-sync flag (should handle the same as empty args)
        with patch('sys.argv', ['smarthome_cli', '--no-sync']), \
             patch('smarthome_cli.main_prompt') as mock_main_prompt:

            # Simulate calling from command line, confirm shows main prompt
            main()
            mock_main_prompt.assert_called_once()

    def test_api_arg(self):
        # Mock --api arg (should call api_client.main to parse remaining args)
        with patch('sys.argv', ['smarthome_cli', '--api']), \
             patch('smarthome_cli.api_client_main') as mock_api_main:

            # Simulate calling from command line, confirm calls api_client.main
            main()
            mock_api_main.assert_called_once()

        # Mock --no-sync flag before --api arg (should handle the same)
        with patch('sys.argv', ['smarthome_cli', '--no-sync', '--api']), \
             patch('smarthome_cli.api_client_main') as mock_api_main:

            # Simulate calling from command line, confirm calls api_client.main
            main()
            mock_api_main.assert_called_once()

    def test_provision_arg(self):
        # Mock --provision arg (should call provision.main to parse remaining args)
        with patch('sys.argv', ['smarthome_cli', '--provision']), \
             patch('smarthome_cli.provision_main') as mock_provision_main:

            # Simulate calling from command line, confirm calls provision.main
            main()
            mock_provision_main.assert_called_once()

        # Mock --no-sync flag before --provision arg (should handle the same)
        with patch('sys.argv', ['smarthome_cli', '--no-sync', '--provision']), \
             patch('smarthome_cli.provision_main') as mock_provision_main:

            # Simulate calling from command line, confirm calls provision.main
            main()
            mock_provision_main.assert_called_once()

    def test_config_arg(self):
        # Mock --config arg (should call config_generator.main to show prompt)
        with patch('sys.argv', ['smarthome_cli', '--config']), \
             patch('smarthome_cli.config_generator_main') as mock_config_main:

            # Simulate calling from command line, confirm calls config_generator.main
            main()
            mock_config_main.assert_called_once()

        # Mock --no-sync flag before --config arg (should handle the same)
        with patch('sys.argv', ['smarthome_cli', '--no-sync', '--config']), \
             patch('smarthome_cli.config_generator_main') as mock_config_main:

            # Simulate calling from command line, confirm calls config_generator.main
            main()
            mock_config_main.assert_called_once()

    def test_invalid_arg(self):
        # Mock invalid arg (should print example usage)
        with patch('sys.argv', ['smarthome_cli', '--invalid']), \
             patch('smarthome_cli.main_prompt') as mock_main_prompt, \
             patch('smarthome_cli.api_client_main') as mock_api_main, \
             patch('smarthome_cli.provision_main') as mock_provision_main, \
             patch('smarthome_cli.config_generator_main') as mock_config_main, \
             patch('builtins.print') as mock_print:

            # Simulate calling from command line
            main()

            # Confirm does not call any prompt function
            mock_main_prompt.assert_not_called()
            mock_api_main.assert_not_called()
            mock_provision_main.assert_not_called()
            mock_config_main.assert_not_called()

            # Confirm called print 4 times (example usage)
            self.assertEqual(mock_print.call_count, 4)


class TestMainPrompt(TestCase):
    '''Tests the main menu prompt, confirms options call correct function'''

    def setUp(self):
        # Mock replaces .ask() method to simulate user input
        self.mock_ask = MagicMock()

    def test_api_prompt(self):
        # Mock user selecting "API client", then "Done" (exit main menu loop)
        self.mock_ask.unsafe_ask.side_effect = ['API client', 'Done']

        with patch('os.path.exists', return_value=True), \
             patch('questionary.select', return_value=self.mock_ask), \
             patch('smarthome_cli.api_prompt') as mock_api_prompt:

            # Run prompt, will complete immediately with mock input
            main_prompt()

            # Confirm api_prompt was called
            mock_api_prompt.assert_called_once()

    def test_manage_nodes_prompt(self):
        # Mock user selecting "Manage nodes", then "Done" (exit main menu loop)
        self.mock_ask.unsafe_ask.side_effect = ['Manage nodes', 'Done']

        with patch('os.path.exists', return_value=True), \
             patch('questionary.select', return_value=self.mock_ask), \
             patch('smarthome_cli.manage_nodes_prompt') as mock_manage_nodes_prompt:

            # Run prompt, will complete immediately with mock input
            main_prompt()

            # Confirm manage_nodes_prompt was called
            mock_manage_nodes_prompt.assert_called_once()

    def test_manage_schedule_keywords_prompt(self):
        # Mock user selecting "Manage schedule keywords", then "Done" (exit
        # main menu loop)
        self.mock_ask.unsafe_ask.side_effect = [
            'Manage schedule keywords',
            'Done'
        ]

        with patch('os.path.exists', return_value=True), \
             patch('questionary.select', return_value=self.mock_ask), \
             patch('smarthome_cli.manage_keywords_prompt') as mock_keywords_prompt:

            # Run prompt, will complete immediately with mock input
            main_prompt()

            # Confirm manage_keywords_prompt was called
            mock_keywords_prompt.assert_called_once()

    def test_settings_prompt(self):
        # Mock user selecting "Settings", then "Done" (exit main menu loop)
        self.mock_ask.unsafe_ask.side_effect = ['Settings', 'Done']

        with patch('os.path.exists', return_value=True), \
             patch('questionary.select', return_value=self.mock_ask), \
             patch('smarthome_cli.settings_prompt') as mock_settings_prompt:

            # Run prompt, will complete immediately with mock input
            main_prompt()

            # Confirm settings_prompt was called
            mock_settings_prompt.assert_called_once()


class TestInitialSetup(TestCase):
    '''Tests the setup prompt called when cli_config.json is missing'''

    def setUp(self):
        # Mock replaces .ask() method to simulate user input
        self.mock_ask = MagicMock()

    def test_automatically_shows_setup_prompt(self):
        # Mock user selecting "Done" at main menu prompt (exit loop)
        self.mock_ask.unsafe_ask.return_value = 'Done'

        # Mock os.path.exists to return False (simulate missing cli_config.json)
        # Mock get_cli_config_path to return mock path in temp directory
        with patch('os.path.exists', return_value=False), \
             patch('smarthome_cli.get_cli_config_path', return_value=mock_cli_config_path), \
             patch('questionary.select', return_value=self.mock_ask), \
             patch('smarthome_cli.setup_prompt') as mock_setup_prompt:

            # Run prompt, will complete immediately with mock input
            main_prompt()

            # Confirm setup prompt was called (cli_config.json missing)
            mock_setup_prompt.assert_called_once()

        # Mock os.path.exists to return True (simulate cli_config.json exists)
        with patch('os.path.exists', return_value=True), \
             patch('questionary.select', return_value=self.mock_ask), \
             patch('smarthome_cli.setup_prompt') as mock_setup_prompt:

            # Run prompt, will complete immediately with mock input
            main_prompt()

            # Confirm setup prompt was NOT called (cli_config.json exists)
            mock_setup_prompt.assert_not_called()

    def test_setup_prompt(self):
        # Simulate user selecting "Yes" at each confirmation
        self.mock_ask.unsafe_ask.return_value = True

        # Mock prompt functions to confirm called
        with patch('questionary.confirm', return_value=self.mock_ask), \
             patch('smarthome_cli.config_directory_prompt') as mock_config_prompt, \
             patch('smarthome_cli.webrepl_password_prompt') as mock_webrepl_prompt, \
             patch('smarthome_cli.django_address_prompt') as mock_django_prompt, \
             patch('smarthome_cli.cli_config.sync_from_django') as mock_sync, \
             patch('smarthome_cli.cli_config.write_cli_config_to_disk') as mock_write_to_disk:

            # Run prompt, will complete immediately
            setup_prompt()

            # Confirm all prompt functions were called
            mock_config_prompt.assert_called_once()
            mock_webrepl_prompt.assert_called_once()
            mock_django_prompt.assert_called_once()
            mock_sync.assert_called_once()

            # Confirm cli_config.json was written to disk
            mock_write_to_disk.assert_called_once()

    def test_setup_prompt_use_defaults(self):
        # Simulate user selecting "No" at each confirmation
        self.mock_ask.unsafe_ask.return_value = False

        # Mock prompt functions to confirm called
        with patch('questionary.confirm', return_value=self.mock_ask), \
             patch('smarthome_cli.config_directory_prompt') as mock_config_prompt, \
             patch('smarthome_cli.webrepl_password_prompt') as mock_webrepl_prompt, \
             patch('smarthome_cli.django_address_prompt') as mock_django_prompt, \
             patch('smarthome_cli.cli_config.sync_from_django') as mock_sync, \
             patch('smarthome_cli.cli_config.write_cli_config_to_disk') as mock_write_to_disk:

            # Run prompt, will complete immediately
            setup_prompt()

            # Confirm no prompt functions were called
            mock_config_prompt.assert_not_called()
            mock_webrepl_prompt.assert_not_called()
            mock_django_prompt.assert_not_called()
            mock_sync.assert_not_called()

            # Confirm cli_config.json was written to disk
            mock_write_to_disk.assert_called_once()


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
             patch('smarthome_cli.delete_node_prompt') as mock_delete_node_prompt:

            # Run prompt, will complete immediately with mock input
            manage_nodes_prompt()

            # Confirm delete_node_prompt was called with selected node + mock password
            mock_delete_node_prompt.assert_called_once()

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


class TestManageScheduleKeywordsPrompt(TestCase):
    '''Tests the schedule keywords prompt, confirms options call correct function'''

    def setUp(self):
        # Mock replaces .ask() method to simulate user input
        self.mock_ask = MagicMock()

    def test_add_schedule_keyword(self):
        # Mock user selecting "Add new schedule keyword", entering keyword name
        # and timestamp, then selecting "Done" (exit loop)
        self.mock_ask.unsafe_ask.side_effect = [
            'Add new schedule keyword',
            'NewName',
            '12:34',
            'Done'
        ]

        with patch('questionary.select', return_value=self.mock_ask), \
             patch('questionary.text', return_value=self.mock_ask), \
             patch('questionary.confirm', return_value=self.mock_ask), \
             patch('smarthome_cli.cli_config.add_schedule_keyword') as mock_add_keyword:

            # Run prompt, will complete immediately with mock input
            manage_keywords_prompt()

            # Confirm cli_config.add_schedule_keyword was called with user input
            mock_add_keyword.assert_called_once_with('NewName', '12:34')

    def test_edit_schedule_keyword_change_both(self):
        # Mock user selecting "Edit schedule keyword", selecting keyword name,
        # changing both name and timestamp, then selecting "Done" (exit loop)
        self.mock_ask.unsafe_ask.side_effect = [
            'Edit schedule keyword',
            'sleep',
            True,
            'NewName',
            True,
            '12:34',
            'Done'
        ]

        with patch('questionary.select', return_value=self.mock_ask), \
             patch('questionary.text', return_value=self.mock_ask), \
             patch('questionary.confirm', return_value=self.mock_ask), \
             patch('smarthome_cli.cli_config.edit_schedule_keyword') as mock_edit_keyword:

            # Run prompt, will complete immediately with mock input
            manage_keywords_prompt()

            # Confirm cli_config.edit_schedule_keyword was called with user input
            mock_edit_keyword.assert_called_once_with('sleep', 'NewName', '12:34')

    def test_edit_schedule_keyword_change_name(self):
        # Mock user selecting "Edit schedule keyword", selecting keyword name,
        # changing name but not timestamp, then selecting "Done" (exit loop)
        self.mock_ask.unsafe_ask.side_effect = [
            'Edit schedule keyword',
            'sleep',
            True,
            'NewName',
            False,
            'Done'
        ]

        with patch('questionary.select', return_value=self.mock_ask), \
             patch('questionary.text', return_value=self.mock_ask), \
             patch('questionary.confirm', return_value=self.mock_ask), \
             patch('smarthome_cli.cli_config.edit_schedule_keyword') as mock_edit_keyword:

            # Run prompt, will complete immediately with mock input
            manage_keywords_prompt()

            # Confirm cli_config.edit_schedule_keyword was called with user input
            mock_edit_keyword.assert_called_once_with('sleep', 'NewName', '22:00')

    def test_edit_schedule_keyword_change_timestamp(self):
        # Mock user selecting "Edit schedule keyword", selecting keyword name,
        # changing timestamp but not name, then selecting "Done" (exit loop)
        self.mock_ask.unsafe_ask.side_effect = [
            'Edit schedule keyword',
            'sleep',
            False,
            True,
            '12:34',
            'Done'
        ]

        with patch('questionary.select', return_value=self.mock_ask), \
             patch('questionary.text', return_value=self.mock_ask), \
             patch('questionary.confirm', return_value=self.mock_ask), \
             patch('smarthome_cli.cli_config.edit_schedule_keyword') as mock_edit_keyword:

            # Run prompt, will complete immediately with mock input
            manage_keywords_prompt()

            # Confirm cli_config.edit_schedule_keyword was called with user input
            mock_edit_keyword.assert_called_once_with('sleep', 'sleep', '12:34')

    def test_delete_schedule_keyword(self):
        # Mock user selecting "Delete schedule keyword", selecting keyword name,
        # then selecting "Done" (exit loop)
        self.mock_ask.unsafe_ask.side_effect = [
            'Delete schedule keyword',
            'sleep',
            'Done'
        ]

        with patch('questionary.select', return_value=self.mock_ask), \
             patch('questionary.text', return_value=self.mock_ask), \
             patch('smarthome_cli.cli_config.remove_schedule_keyword') as mock_rm_keyword:

            # Run prompt, will complete immediately with mock input
            manage_keywords_prompt()

            # Confirm cli_config.remove_schedule_keyword was called with user selection
            mock_rm_keyword.assert_called_once_with('sleep')


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
            settings_prompt()

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
            settings_prompt()

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
            settings_prompt()

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
             patch('questionary.path', return_value=self.mock_ask), \
             patch('smarthome_cli.cli_config.set_config_directory') as mock_set_dir:

            # Run prompt, will complete immediately with mock input
            settings_prompt()

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
            settings_prompt()

            # Confirm cli_config.set_webrepl_password was called with user input
            mock_set_password.assert_called_once_with('password')

    def test_visible_prompt_options(self):
        # Create mock cli_config.json with no django backend configured
        mock_cli_config_no_backend = deepcopy(mock_cli_config)
        del mock_cli_config_no_backend['django_backend']

        # Mock user selecting "Done" (exit loop)
        self.mock_ask.unsafe_ask.return_value = 'Done'

        # Mock cli_config.json to simulate no django backend configured
        # Mock questionary.select to confirm visible options
        with patch('smarthome_cli.cli_config.config', mock_cli_config_no_backend), \
             patch('questionary.select', return_value=self.mock_ask) as mock_select:

            # Run prompt, will complete immediately with mock input
            settings_prompt()

            # Confirm did not display django sync options
            mock_select.assert_called_once_with(
                "Settings menu",
                choices=[
                    "Set django address",
                    "Change config directory",
                    "Change webrepl password",
                    "Done"
                ]
            )

        # Repeat test without mocking cli_config.json (simulate backend configured)
        with patch('questionary.select', return_value=self.mock_ask) as mock_select:

            # Run prompt, will complete immediately with mock input
            settings_prompt()

            # Confirm displayed all options
            mock_select.assert_called_once_with(
                "Settings menu",
                choices=[
                    "Set django address",
                    "Sync nodes and keywords from django",
                    "Download all config files from django",
                    "Change config directory",
                    "Change webrepl password",
                    "Done"
                ]
            )


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
            mock_confirm.return_value.ask.return_value = True

            # Call function
            create_new_node_prompt()

            # Confirm GenerateConfigFile was instantiated
            mock_generator_class.assert_called_once()

            # Confirm prompt was shown, config was written to disk
            mock_generator.run_prompt.assert_called_once()
            mock_generator.write_to_disk.assert_called_once()

            # Confirm requested filename for new config
            mock_get_filename.assert_called_once()

            # Confirm called upload_config_from_disk with filename as arg
            mock_upload_config.assert_called_once_with('mock.json')

    def test_create_new_node_prompt_no_upload(self):
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

            # Answer "No" to "Upload config to ESP32?" prompt
            mock_confirm.return_value.ask.return_value = False

            # Call function
            create_new_node_prompt()

            # Confirm GenerateConfigFile was instantiated
            mock_generator_class.assert_called_once()

            # Confirm prompt was shown, config was written to disk
            mock_generator.run_prompt.assert_called_once()
            mock_generator.write_to_disk.assert_called_once()

            # Confirm did NOT call upload_config_from_disk or get_config_filename
            mock_get_filename.assert_not_called()
            mock_upload_config.assert_not_called()

    def test_create_new_node_prompt_config_failed_validation(self):
        # Create mock GenerateConfigFile instance to confirm methods were called
        # Set passed_validation to False (simulate invalid config file)
        mock_generator = MagicMock()
        mock_generator.run_prompt = MagicMock()
        mock_generator.passed_validation = False
        mock_generator.write_to_disk = MagicMock()
        mock_generator.config = {'metadata': {'id': 'mock_name'}}

        # Mock GenerateConfigFile class to return mock instance
        # Mock helper functions called after user completes config prompts
        with patch('smarthome_cli.GenerateConfigFile', return_value=mock_generator) as mock_generator_class, \
             patch('smarthome_cli.upload_config_from_disk') as mock_upload_config, \
             patch('questionary.confirm', MagicMock()) as mock_confirm:

            # Call function
            create_new_node_prompt()

            # Confirm GenerateConfigFile was instantiated, prompt was shown
            mock_generator_class.assert_called_once()
            mock_generator.run_prompt.assert_called_once()

            # Confirm did NOT write invalid config to disk
            mock_generator.write_to_disk.assert_not_called()

            # Confirm did NOT prompt user to upload invalid config
            mock_confirm.assert_not_called()
            mock_upload_config.assert_not_called()

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

    def test_edit_existing_node_config_no_reupload(self):
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

            # Answer "No" to "Reupload now?" prompt
            mock_confirm.return_value.ask.return_value = False

            # Call function
            edit_node_config_prompt()

            # Confirm requested path to selected node config file
            mock_get_path.assert_called_once_with('node1')

            # Confirm GenerateConfigFile was instantiated with path to config file
            mock_generator_class.assert_called_once_with('node1.json')

            # Confirm prompt was shown, config was written to disk
            mock_generator.run_prompt.assert_called_once()
            mock_generator.write_to_disk.assert_called_once()

            # Confirm did NOT call upload_node
            mock_upload_node.assert_not_called()

    def test_edit_existing_node_config_failed_validation(self):
        # Mock user selecting name of existing node
        self.mock_ask.unsafe_ask.return_value = 'node1'

        # Create mock GenerateConfigFile instance to confirm methods were called
        # Set passed_validation to False (simulate invalid config file)
        mock_generator = MagicMock()
        mock_generator.run_prompt = MagicMock()
        mock_generator.passed_validation = False
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

            # Call function
            edit_node_config_prompt()

            # Confirm requested path to selected node config file
            mock_get_path.assert_called_once_with('node1')

            # Confirm GenerateConfigFile was instantiated with path to config
            # file, confirm prompt was shown
            mock_generator_class.assert_called_once_with('node1.json')
            mock_generator.run_prompt.assert_called_once()

            # Confirm did NOT write invalid config to disk
            mock_generator.write_to_disk.assert_not_called()

            # Confirm did NOT prompt user to upload invalid config
            mock_confirm.assert_not_called()
            mock_upload_node.assert_not_called()

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

    def test_upload_config_from_disk_with_config_path_as_arg(self):
        # Mock user entering IP address
        self.mock_ask.unsafe_ask.side_effect = [
            '192.168.1.123'
        ]

        with patch('questionary.select', return_value=self.mock_ask), \
             patch('questionary.text', return_value=self.mock_ask), \
             patch('smarthome_cli.upload_config_to_ip') as mock_upload_config:

            # Call prompt path to config file as argument
            upload_config_from_disk('node2.json')

            # Confirm called upload_config_to_ip with user-entered IP, absolute
            # path to config file given as argument
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
        mock_connection.close_connection = MagicMock()

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

            # Confirm connection was closed
            mock_connection.close_connection.assert_called_once()

            # Confirm pager was called with decoded log
            mock_pager.assert_called_once_with('mock_log')

            # Confirm opened 'node_log.text' and wrote mock log contents to disk
            mocked_open.assert_called_once_with('node_log.txt', 'w', encoding='utf-8')
            mock_file = mocked_open()
            mock_file.write.assert_called_once_with('mock_log')

    def test_view_log_prompt_dont_save(self):
        # Mock user selecting name of existing node
        self.mock_ask.unsafe_ask.side_effect = [
            'node1'
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
             patch('builtins.open', mock_open()) as mocked_open:

            # Answer "No" to "Save log?" prompt
            mock_confirm.return_value.ask.return_value = False

            # Call function
            view_log_prompt()

            # Confirm Webrepl was instantiated with selected node IP + webrepl password
            mock_webrepl_class.assert_called_once_with('192.168.1.123', 'password')

            # Confirm get_file_mem was called with name of log file
            mock_connection.get_file_mem.assert_called_once_with('app.log')

            # Confirm pager was called with decoded log
            mock_pager.assert_called_once_with('mock_log')

            # Confirm did not open file to write log to disk
            mocked_open.assert_not_called()

    def test_view_log_prompt_connection_error(self):
        # Mock user selecting name of existing node
        self.mock_ask.unsafe_ask.side_effect = [
            'node1'
        ]

        # Create mock Webrepl instance, simulate connection error while reading
        mock_connection = MagicMock()
        mock_connection.get_file_mem = MagicMock(side_effect=OSError)

        # Mock select prompt to return mocked node selection
        # Mock text prompt to return mocked log filename
        # Mock Webrepl class to return mock instance
        # Mock pydoc.pager (called to display log)
        with patch('questionary.select', return_value=self.mock_ask), \
             patch('questionary.text', return_value=self.mock_ask), \
             patch('smarthome_cli.Webrepl', return_value=mock_connection) as mock_webrepl_class, \
             patch('smarthome_cli.pydoc.pager') as mock_pager, \
             patch('questionary.confirm', MagicMock()) as mock_confirm:

            # Answer "No" to "Save log?" prompt
            mock_confirm.return_value.ask.return_value = False

            # Call function
            view_log_prompt()

            # Confirm Webrepl was instantiated with selected node IP + webrepl password
            mock_webrepl_class.assert_called_once_with('192.168.1.123', 'password')

            # Confirm get_file_mem was called with name of log file
            mock_connection.get_file_mem.assert_called_once_with('app.log')

            # Confirm pager was NOT called (exits when connection error occurs)
            mock_pager.assert_not_called()

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

    def test_delete_node_prompt(self):
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
            delete_node_prompt()

            # Confirm cli_config.remove_node was called with both selected nodes
            self.assertEqual(len(mock_remove_node.call_args_list), 2)
            self.assertEqual(mock_remove_node.call_args_list[0][0][0], 'node1')
            self.assertEqual(mock_remove_node.call_args_list[1][0][0], 'node3')

    def test_delete_node_prompt_cancel(self):
        # Mock user checking 2 nodes at checkbox prompt, then selecting "No" at
        # confirmation prompt
        self.mock_ask.unsafe_ask.side_effect = [
            ['node1', 'node3'],
            'No'
        ]

        # Mock checkbox and select prompts to return mocked user input
        # Mock cli_config.remove_node to confirm not called
        with patch('questionary.select', return_value=self.mock_ask), \
             patch('questionary.checkbox', return_value=self.mock_ask), \
             patch('smarthome_cli.cli_config.remove_node') as mock_remove_node:

            # Run prompt, will complete immediately with mock input
            delete_node_prompt()

            # Confirm cli_config.remove_node was NOT called (canceled)
            mock_remove_node.assert_not_called()

    def test_delete_node_prompt_no_django(self):
        # Mock user checking 2 nodes at checkbox prompt, then selecting "Yes"
        # at confirmation prompt
        self.mock_ask.unsafe_ask.side_effect = [
            ['node1', 'node3'],
            'Yes'
        ]

        # Create mock cli_config.json with no django backend configured
        mock_cli_config_no_backend = deepcopy(mock_cli_config)
        del mock_cli_config_no_backend['django_backend']

        # Mock checkbox and select prompts to return mocked user input
        # Mock CliConfigManager _client.post to confirm no request made
        # Mock cli_config.json to simulate no django backend
        with patch('questionary.select', return_value=self.mock_ask), \
             patch('questionary.checkbox', return_value=self.mock_ask), \
             patch('smarthome_cli.cli_config._client', MagicMock()) as mock_client, \
             patch.object(mock_client, 'post') as mock_post, \
             patch('smarthome_cli.cli_config.config', mock_cli_config_no_backend), \
             patch('smarthome_cli.cli_config.write_cli_config_to_disk'):

            # Run prompt, will complete immediately with mock input
            delete_node_prompt()

            # Confirm no post request was made (django not configured)
            mock_post.assert_not_called()
