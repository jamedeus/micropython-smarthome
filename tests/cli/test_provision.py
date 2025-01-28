# pylint: disable=line-too-long, missing-function-docstring, missing-module-docstring, missing-class-docstring

import os
import sys
import json
from copy import deepcopy
from unittest import TestCase
from unittest.mock import patch, MagicMock, mock_open
from argparse import Namespace, ArgumentParser
from provision import parse_args, main
from provision_tools import provision, get_modules
from Webrepl import Webrepl
from mock_cli_config import mock_cli_config

# Get full paths to repository root directory
cli = os.path.split(os.path.dirname(os.path.realpath(__file__)))[0]
repo = os.path.split(cli)[0]


class TestArgParser(TestCase):

    def test_all(self):
        with patch.object(sys, 'argv', ['', '--all']):
            args, _ = parse_args()

        # Confirm all arg is set
        self.assertTrue(args.all)

        # Confirm all other args empty
        self.assertFalse(args.test)
        self.assertFalse(args.node)
        self.assertFalse(args.ip)
        self.assertFalse(args.config)
        self.assertFalse(args.password)

    def test_unit_test(self):
        with patch.object(sys, 'argv', ['', '--test', '192.168.1.123']):
            args, _ = parse_args()

        # Confirm test arg contains target IP
        self.assertTrue(args.test)
        self.assertEqual(args.test, '192.168.1.123')

        # Confirm all other args empty
        self.assertFalse(args.all)
        self.assertFalse(args.node)
        self.assertFalse(args.ip)
        self.assertFalse(args.config)
        self.assertFalse(args.password)

    def test_node_friendly_name(self):
        with patch.object(sys, 'argv', ['', 'node1']):
            args, _ = parse_args()

        # Confirm node arg contains friendly name
        self.assertTrue(args.node)
        self.assertEqual(args.node, 'node1')

        # Confirm all other args empty
        self.assertFalse(args.all)
        self.assertFalse(args.test)
        self.assertFalse(args.ip)
        self.assertFalse(args.config)
        self.assertFalse(args.password)

    def test_manual_parameters(self):
        open('node1.json', 'w', encoding='utf-8')
        cli_args = ['', '--config', 'node1.json', '--ip', '192.168.1.123', '--password', 'hunter2']
        with patch.object(sys, 'argv', cli_args):
            args, _ = parse_args()

        # Confirm parameters matched to correct args
        self.assertEqual(args.config, 'node1.json')
        self.assertEqual(args.ip, '192.168.1.123')
        self.assertEqual(args.password, 'hunter2')

        # Confirm all other args empty
        self.assertFalse(args.all)
        self.assertFalse(args.test)
        self.assertFalse(args.node)
        os.remove('node1.json')

    def test_manual_parameters_config_relative_path(self):
        config_path = os.path.join(mock_cli_config['config_directory'], 'node1.json')
        open(config_path, 'w', encoding='utf-8')
        cli_args = ['', '--config', 'node1.json', '--ip', '192.168.1.123', '--password', 'hunter2']
        with patch.object(sys, 'argv', cli_args):
            args, _ = parse_args()

        # Confirm parameters matched to correct args
        self.assertEqual(args.config, os.path.abspath(config_path))
        self.assertEqual(args.ip, '192.168.1.123')
        self.assertEqual(args.password, 'hunter2')

        # Confirm all other args empty
        self.assertFalse(args.all)
        self.assertFalse(args.test)
        self.assertFalse(args.node)
        os.remove(config_path)

    def test_invalid_ip(self):
        with patch.object(sys, 'argv', ['', '--config', 'node1.json', '--ip', '192.168.1']), \
             self.assertRaises(SystemExit):

            parse_args()

    def test_missing_config_file(self):
        with patch.object(sys, 'argv', ['', '--ip', '192.168.1.123']), \
             self.assertRaises(SystemExit):

            parse_args()

    def test_invalid_config_file(self):
        with patch.object(sys, 'argv', ['', '--config', 'does_not_exist.json', '--ip', '192.168.1.123']), \
             self.assertRaises(SystemExit):
            parse_args()


class TestInstantiation(TestCase):

    def test_provision_all(self):
        # Mock args for --all
        args = Namespace(config=None, ip=None, node=None, all=True, test=None, password=None)

        # Mock provision to do nothing, mock parse_args to return mock args,
        # mock os.path.exists to return True (pretend config file exists), mock
        # open to return empty dict (mock config file contents)
        mock_file = mock_open(read_data=json.dumps({}))
        response = {'message': 'Upload complete.', 'status': 200}
        with patch('provision.provision', MagicMock(return_value=response)) as mock_provision, \
             patch('provision.parse_args', return_value=(args, '')), \
             patch('helper_functions.os.path.exists', return_value=True), \
             patch('builtins.open', mock_file):

            # Confirm provision called once for each node
            main()
            self.assertEqual(mock_provision.call_count, 3)
            called_ips = [c[1]['ip'] for c in mock_provision.call_args_list]
            self.assertCountEqual(
                called_ips,
                ['192.168.1.123', '192.168.1.234', '192.168.1.111']
            )

    def test_provision_friendly_name(self):
        # Mock args with node friendly name
        args = Namespace(config=None, ip=None, node='node1', all=None, test=None, password=None)

        # Mock provision to do nothing, mock parse_args to return mock args,
        # mock os.path.exists to return True (pretend config file exists), mock
        # open to return empty dict (mock config file contents)
        mock_file = mock_open(read_data=json.dumps({}))
        response = {'message': 'Upload complete.', 'status': 200}
        with patch('provision.provision', MagicMock(return_value=response)) as mock_provision, \
             patch('provision.parse_args', return_value=(args, '')), \
             patch('helper_functions.os.path.exists', return_value=True), \
             patch('builtins.open', mock_file):

            # Confirm provision called once with expected IP
            main()
            self.assertEqual(mock_provision.call_count, 1)
            self.assertEqual(mock_provision.call_args[1]['ip'], '192.168.1.123')

    def test_provision_friendly_name_missing_config_file(self):
        # Mock args with node friendly name
        args = Namespace(config=None, ip=None, node='node1', all=None, test=None, password=None)

        # Mock provision to do nothing, mock parse_args to return mock args,
        # mock cli_config.load_node_config_file to simulate file missing from
        # disk (django not configured, no prompt to download), mock print to
        # confirm expected error appears
        with patch('provision.provision') as mock_provision, \
             patch('provision.parse_args', return_value=(args, '')), \
             patch('provision.cli_config.load_node_config_file', side_effect=FileNotFoundError), \
             patch('builtins.print') as mock_print:

            # Confirm provision was NOT called
            main()
            mock_provision.assert_not_called()

            # Confirm expected error was printed to console
            mock_print.assert_called_with('ERROR: node1 config file missing from disk')

    def test_provision_friendly_name_download_missing_config_from_django(self):
        # Mock args with node friendly name
        args = Namespace(config=None, ip=None, node='node1', all=None, test=None, password=None)

        # Mock questionary.confirm.ask() to simulate user selecting Yes when
        # prompted about downloading missing config file from django
        mock_confirm = MagicMock()
        mock_confirm.ask.return_value = True

        # Mock provision to do nothing, mock parse_args to return mock args,
        # mock os.path.exists to return False (simulate missing config file),
        # mock questionary.confirm to simulate user selecting Yes, mock
        # cli_config download method to confirm called when user selects Yes
        response = {'message': 'Upload complete.', 'status': 200}
        with patch('provision.provision', MagicMock(return_value=response)) as mock_provision, \
             patch('provision.parse_args', return_value=(args, '')), \
             patch('helper_functions.os.path.exists', return_value=False), \
             patch('questionary.confirm', return_value=mock_confirm), \
             patch('provision.cli_config.download_node_config_file_from_django') as mock_download:

            # Mock cli_config download method to return mock config
            mock_download.return_value = {'metadata': {'id': 'Node1'}}

            # Confirm downloaded missing config from django
            main()
            mock_download.assert_called_once_with('192.168.1.123')

            # Confirm provision called once with expected IP
            self.assertEqual(mock_provision.call_count, 1)
            self.assertEqual(mock_provision.call_args[1]['ip'], '192.168.1.123')

    def test_provision_unit_tests(self):
        # Expected test modules
        test_modules = {
            os.path.join(repo, 'devices', 'Tplink.py'): 'Tplink.py',
            os.path.join(repo, 'devices', 'Device.py'): 'Device.py',
            os.path.join(repo, 'devices', 'DeviceWithLoop.py'): 'DeviceWithLoop.py',
            os.path.join(repo, 'devices', 'DimmableLight.py'): 'DimmableLight.py',
            os.path.join(repo, 'devices', 'TasmotaRelay.py'): 'TasmotaRelay.py',
            os.path.join(repo, 'devices', 'Relay.py'): 'Relay.py',
            os.path.join(repo, 'devices', 'HttpGet.py'): 'HttpGet.py',
            os.path.join(repo, 'devices', 'DesktopTarget.py'): 'DesktopTarget.py',
            os.path.join(repo, 'devices', 'LedStrip.py'): 'LedStrip.py',
            os.path.join(repo, 'devices', 'ApiTarget.py'): 'ApiTarget.py',
            os.path.join(repo, 'devices', 'Wled.py'): 'Wled.py',
            os.path.join(repo, 'sensors', 'MotionSensor.py'): 'MotionSensor.py',
            os.path.join(repo, 'sensors', 'Sensor.py'): 'Sensor.py',
            os.path.join(repo, 'sensors', 'SensorWithLoop.py'): 'SensorWithLoop.py',
            os.path.join(repo, 'sensors', 'Thermostat.py'): 'Thermostat.py',
            os.path.join(repo, 'sensors', 'Si7021.py'): 'Si7021.py',
            os.path.join(repo, 'sensors', 'Dht22.py'): 'Dht22.py',
            os.path.join(repo, 'sensors', 'Dummy.py'): 'Dummy.py',
            os.path.join(repo, 'sensors', 'LoadCell.py'): 'LoadCell.py',
            os.path.join(repo, 'sensors', 'Switch.py'): 'Switch.py',
            os.path.join(repo, 'sensors', 'DesktopTrigger.py'): 'DesktopTrigger.py',
            os.path.join(repo, 'devices', 'IrBlaster.py'): 'IrBlaster.py',
            os.path.join(repo, 'tests', 'firmware', 'test_device_desktop_target.py'): 'test_device_desktop_target.py',
            os.path.join(repo, 'tests', 'firmware', 'test_device_device.py'): 'test_device_device.py',
            os.path.join(repo, 'tests', 'firmware', 'test_device_dimmablelight.py'): 'test_device_dimmablelight.py',
            os.path.join(repo, 'tests', 'firmware', 'test_device_tplink.py'): 'test_device_tplink.py',
            os.path.join(repo, 'tests', 'firmware', 'test_sensor_desktop_trigger.py'): 'test_sensor_desktop_trigger.py',
            os.path.join(repo, 'tests', 'firmware', 'test_sensor_switch.py'): 'test_sensor_switch.py',
            os.path.join(repo, 'tests', 'firmware', 'test_sensor_sensor.py'): 'test_sensor_sensor.py',
            os.path.join(repo, 'tests', 'firmware', 'test_sensor_sensor_with_loop.py'): 'test_sensor_sensor_with_loop.py',
            os.path.join(repo, 'tests', 'firmware', 'test_sensor_thermostat.py'): 'test_sensor_thermostat.py',
            os.path.join(repo, 'tests', 'firmware', 'test_sensor_si7021.py'): 'test_sensor_si7021.py',
            os.path.join(repo, 'tests', 'firmware', 'test_sensor_dht22.py'): 'test_sensor_dht22.py',
            os.path.join(repo, 'tests', 'firmware', 'test_device_apitarget.py'): 'test_device_apitarget.py',
            os.path.join(repo, 'tests', 'firmware', 'test_device_wled.py'): 'test_device_wled.py',
            os.path.join(repo, 'tests', 'firmware', 'test_device_relay.py'): 'test_device_relay.py',
            os.path.join(repo, 'tests', 'firmware', 'test_device_http_get.py'): 'test_device_http_get.py',
            os.path.join(repo, 'tests', 'firmware', 'test_core_config.py'): 'test_core_config.py',
            os.path.join(repo, 'tests', 'firmware', 'test_api_api.py'): 'test_api_api.py',
            os.path.join(repo, 'tests', 'firmware', 'test_device_irblaster.py'): 'test_device_irblaster.py',
            os.path.join(repo, 'tests', 'firmware', 'test_sensor_motionsensor.py'): 'test_sensor_motionsensor.py',
            os.path.join(repo, 'tests', 'firmware', 'test_device_ledstrip.py'): 'test_device_ledstrip.py',
            os.path.join(repo, 'tests', 'firmware', 'test_sensor_dummy.py'): 'test_sensor_dummy.py',
            os.path.join(repo, 'tests', 'firmware', 'test_sensor_load_cell.py'): 'test_sensor_load_cell.py',
            os.path.join(repo, 'tests', 'firmware', 'test_device_tasmota_relay.py'): 'test_device_tasmota_relay.py',
            os.path.join(repo, 'tests', 'firmware', 'test_core_boot.py'): 'test_core_boot.py',
            os.path.join(repo, 'tests', 'firmware', 'test_core_main.py'): 'test_core_main.py',
            os.path.join(repo, 'tests', 'firmware', 'test_core_softwaretimer.py'): 'test_core_softwaretimer.py',
            os.path.join(repo, 'tests', 'firmware', 'test_core_util.py'): 'test_core_util.py',
            os.path.join(repo, 'tests', 'firmware', 'test_core_group.py'): 'test_core_group.py',
            os.path.join(repo, 'tests', 'firmware', 'test_core_wifi_setup.py'): 'test_core_wifi_setup.py',
            os.path.join(repo, 'core', 'Instance.py'): 'Instance.py',
            os.path.join(repo, 'core', 'Config.py'): 'Config.py',
            os.path.join(repo, 'core', 'Group.py'): 'Group.py',
            os.path.join(repo, 'core', 'SoftwareTimer.py'): 'SoftwareTimer.py',
            os.path.join(repo, 'core', 'app_context.py'): 'app_context.py',
            os.path.join(repo, 'core', 'Api.py'): 'Api.py',
            os.path.join(repo, 'core', 'util.py'): 'util.py',
            os.path.join(repo, 'tests', 'firmware', 'unit_test_main.py'): 'main.py'
        }

        # Mock args to upload unit tests to 192.168.1.123
        args = Namespace(config=None, ip=None, node=None, all=None, test='192.168.1.123', password=None)

        # Mock provision to do nothing, mock parse_args to return mock args,
        # mock open to return empty dict (config file)
        mock_file = mock_open(read_data=json.dumps({}))
        response = {'message': 'Upload complete.', 'status': 200}
        with patch('provision.provision', MagicMock(return_value=response)) as mock_provision, \
             patch('provision.parse_args', return_value=(args, '')), \
             patch('builtins.open', mock_file):

            # Confirm called once with given IP + test modules
            main()
            args = mock_provision.call_args[0]
            self.assertEqual(args[0], '192.168.1.123')
            self.assertEqual(args[3], test_modules)
            mock_provision.assert_called_once()

    def test_provision_manual_args(self):
        # Mock config file contents with ID parameter set (used as key in cli_config.json nodes section)
        mock_file_contents = {'metadata': {'id': 'Node4'}}

        # Mock file object to simulate config arg
        mock_file = mock_open(read_data=json.dumps(mock_file_contents))
        mock_file.name = '../config/node4.json'

        # Mock args with manually specified config file, IP, password
        args = Namespace(
            config=mock_file.name,
            ip='192.168.1.123',
            node=None,
            all=None,
            test=None,
            password='hunter2'
        )

        # Create copy of mock_cli_config (will be modified in tests)
        mock_cli_config_copy = deepcopy(mock_cli_config)

        # Confirm ID from mock config not in cli_config.json nodes section
        self.assertNotIn('node4', mock_cli_config_copy['nodes'].keys())

        # Mock provision to do nothing, mock parse_args to return mock args
        # Mock cli_config.json contents (allows reading changes to mock)
        # Mock open, json.load and os.path.exists to return mock_file_contents
        # Mock cli_config._client.post to check POST request body
        response = {'message': 'Upload complete.', 'status': 200}
        with patch('provision.provision', MagicMock(return_value=response)) as mock_provision, \
             patch('provision.parse_args', return_value=(args, '')), \
             patch('provision.cli_config.config', mock_cli_config_copy), \
             patch('provision.json.load', MagicMock(return_value=mock_file_contents)), \
             patch('builtins.open', mock_file), \
             patch('os.path.exists', return_value=True), \
             patch('provision.cli_config._client.post') as mock_post:

            # Confirm provision called once with expected IP, password, config
            main()
            self.assertEqual(mock_provision.call_count, 1)
            kwargs = mock_provision.call_args[1]
            self.assertEqual(kwargs['ip'], '192.168.1.123')
            self.assertEqual(kwargs['password'], 'hunter2')
            self.assertEqual(kwargs['config'], mock_file_contents)

            # Confirm node was uploaded to django database
            self.assertEqual(mock_post.call_count, 1)
            request_args = mock_post.call_args
            self.assertEqual(request_args[0][0], 'http://192.168.1.100/add_node')
            self.assertEqual(
                request_args[1]['json'],
                {
                    'ip': '192.168.1.123',
                    'config': mock_file_contents
                }
            )

        # Confirm ID from mock config was added to cli_config.json nodes section
        self.assertIn('node4', mock_cli_config_copy['nodes'].keys())
        self.assertEqual(mock_cli_config_copy['nodes']['node4'], '192.168.1.123')

    def test_provision_manual_args_upload_failed(self):
        # Mock config file contents with ID parameter set (used as key in cli_config.json nodes section)
        mock_file_contents = {'metadata': {'id': 'Node4'}}

        # Mock file object to simulate config arg
        mock_file = mock_open(read_data=json.dumps(mock_file_contents))
        mock_file.name = '../config/node4.json'

        # Mock args with manually specified config file, IP, password
        args = Namespace(
            config=mock_file.name,
            ip='192.168.1.123',
            node=None,
            all=None,
            test=None,
            password='hunter2'
        )

        # Create copy of mock_cli_config (will be modified in tests)
        mock_cli_config_copy = deepcopy(mock_cli_config)

        # Confirm ID from mock config not in cli_config.json nodes section
        self.assertNotIn('node4', mock_cli_config_copy['nodes'].keys())

        # Mock provision to simulate failed upload, mock parse_args to return mock args
        # Mock cli_config.json contents (allows reading changes to mock)
        # Mock open, json.load and os.path.exists to return mock_file_contents
        # Mock cli_config._client.post to check POST request body
        response = {'message': 'Error: Unable to connect to node.', 'status': 404}
        with patch('provision.provision', MagicMock(return_value=response)) as mock_provision, \
             patch('provision.parse_args', return_value=(args, '')), \
             patch('provision.cli_config.config', mock_cli_config_copy), \
             patch('provision.json.load', MagicMock(return_value=mock_file_contents)), \
             patch('builtins.open', mock_file), \
             patch('os.path.exists', return_value=True), \
             patch('provision.cli_config._client.post') as mock_post:

            # Confirm provision called once with expected IP, password, config
            main()
            self.assertEqual(mock_provision.call_count, 1)
            kwargs = mock_provision.call_args[1]
            self.assertEqual(kwargs['ip'], '192.168.1.123')
            self.assertEqual(kwargs['password'], 'hunter2')
            self.assertEqual(kwargs['config'], mock_file_contents)

            # Confirm node was NOT uploaded to django database (only uploads if
            # successfully provisioned node)
            mock_post.assert_not_called()

        # Confirm ID from mock config was NOT added to cli_config.json nodes
        # section (only adds if successfully uploaded to node)
        self.assertNotIn('node4', mock_cli_config_copy['nodes'].keys())

    def test_provision_no_args(self):
        # Mock args, all blank
        args = Namespace(config=None, ip=None, node=None, all=None, test=None, password=None)

        # Mock parser object
        mock_parser = MagicMock(spec=ArgumentParser)

        # Mock parse_args to return blank args + mock parser
        with patch('provision.parse_args', return_value=(args, mock_parser)):
            main()
            # Confirm print_help was called
            mock_parser.print_help.assert_called()


class TestGetModules(TestCase):
    def setUp(self):
        unit_test_config_path = os.path.join(repo, "util", "unit-test-config.json")
        with open(unit_test_config_path, 'r', encoding='utf-8') as file:
            self.config = json.load(file)

    def test_get_modules_full_config(self):

        expected_modules = {
            os.path.join(repo, 'devices', 'ApiTarget.py'): 'ApiTarget.py',
            os.path.join(repo, 'devices', 'Wled.py'): 'Wled.py',
            os.path.join(repo, 'devices', 'TasmotaRelay.py'): 'TasmotaRelay.py',
            os.path.join(repo, 'sensors', 'MotionSensor.py'): 'MotionSensor.py',
            os.path.join(repo, 'sensors', 'Dummy.py'): 'Dummy.py',
            os.path.join(repo, 'devices', 'Device.py'): 'Device.py',
            os.path.join(repo, 'devices', 'DeviceWithLoop.py'): 'DeviceWithLoop.py',
            os.path.join(repo, 'sensors', 'Switch.py'): 'Switch.py',
            os.path.join(repo, 'sensors', 'DesktopTrigger.py'): 'DesktopTrigger.py',
            os.path.join(repo, 'devices', 'Relay.py'): 'Relay.py',
            os.path.join(repo, 'devices', 'Tplink.py'): 'Tplink.py',
            os.path.join(repo, 'devices', 'DesktopTarget.py'): 'DesktopTarget.py',
            os.path.join(repo, 'sensors', 'Thermostat.py'): 'Thermostat.py',
            os.path.join(repo, 'sensors', 'Si7021.py'): 'Si7021.py',
            os.path.join(repo, 'sensors', 'Sensor.py'): 'Sensor.py',
            os.path.join(repo, 'sensors', 'SensorWithLoop.py'): 'SensorWithLoop.py',
            os.path.join(repo, 'devices', 'LedStrip.py'): 'LedStrip.py',
            os.path.join(repo, 'devices', 'DimmableLight.py'): 'DimmableLight.py',
            os.path.join(repo, 'devices', 'HttpGet.py'): 'HttpGet.py',
            os.path.join(repo, 'devices', 'IrBlaster.py'): 'IrBlaster.py',
            os.path.join(repo, 'core', 'Instance.py'): 'Instance.py',
            os.path.join(repo, 'core', 'Config.py'): 'Config.py',
            os.path.join(repo, 'core', 'Group.py'): 'Group.py',
            os.path.join(repo, 'core', 'SoftwareTimer.py'): 'SoftwareTimer.py',
            os.path.join(repo, 'core', 'app_context.py'): 'app_context.py',
            os.path.join(repo, 'core', 'Api.py'): 'Api.py',
            os.path.join(repo, 'core', 'util.py'): 'util.py',
            os.path.join(repo, 'core', 'main.py'): 'main.py'
        }

        modules = get_modules(self.config, repo)
        self.assertEqual(modules, expected_modules)

    def test_get_modules_empty_config(self):
        expected_modules = {
            os.path.join(repo, 'core', 'Config.py'): 'Config.py',
            os.path.join(repo, 'core', 'Group.py'): 'Group.py',
            os.path.join(repo, 'core', 'SoftwareTimer.py'): 'SoftwareTimer.py',
            os.path.join(repo, 'core', 'app_context.py'): 'app_context.py',
            os.path.join(repo, 'core', 'Api.py'): 'Api.py',
            os.path.join(repo, 'core', 'util.py'): 'util.py',
            os.path.join(repo, 'core', 'main.py'): 'main.py'
        }

        # Should only return core modules, no devices or sensors
        modules = get_modules({}, repo)
        self.assertEqual(modules, expected_modules)

    def test_get_modules_no_ir_blaster(self):
        del self.config['ir_blaster']

        expected_modules = {
            os.path.join(repo, 'devices', 'ApiTarget.py'): 'ApiTarget.py',
            os.path.join(repo, 'devices', 'Wled.py'): 'Wled.py',
            os.path.join(repo, 'devices', 'TasmotaRelay.py'): 'TasmotaRelay.py',
            os.path.join(repo, 'sensors', 'MotionSensor.py'): 'MotionSensor.py',
            os.path.join(repo, 'sensors', 'Dummy.py'): 'Dummy.py',
            os.path.join(repo, 'devices', 'Device.py'): 'Device.py',
            os.path.join(repo, 'devices', 'DeviceWithLoop.py'): 'DeviceWithLoop.py',
            os.path.join(repo, 'sensors', 'Switch.py'): 'Switch.py',
            os.path.join(repo, 'sensors', 'DesktopTrigger.py'): 'DesktopTrigger.py',
            os.path.join(repo, 'devices', 'Relay.py'): 'Relay.py',
            os.path.join(repo, 'devices', 'Tplink.py'): 'Tplink.py',
            os.path.join(repo, 'devices', 'DesktopTarget.py'): 'DesktopTarget.py',
            os.path.join(repo, 'sensors', 'Thermostat.py'): 'Thermostat.py',
            os.path.join(repo, 'sensors', 'Si7021.py'): 'Si7021.py',
            os.path.join(repo, 'sensors', 'Sensor.py'): 'Sensor.py',
            os.path.join(repo, 'sensors', 'SensorWithLoop.py'): 'SensorWithLoop.py',
            os.path.join(repo, 'devices', 'LedStrip.py'): 'LedStrip.py',
            os.path.join(repo, 'devices', 'DimmableLight.py'): 'DimmableLight.py',
            os.path.join(repo, 'devices', 'HttpGet.py'): 'HttpGet.py',
            os.path.join(repo, 'core', 'Instance.py'): 'Instance.py',
            os.path.join(repo, 'core', 'Config.py'): 'Config.py',
            os.path.join(repo, 'core', 'Group.py'): 'Group.py',
            os.path.join(repo, 'core', 'SoftwareTimer.py'): 'SoftwareTimer.py',
            os.path.join(repo, 'core', 'app_context.py'): 'app_context.py',
            os.path.join(repo, 'core', 'Api.py'): 'Api.py',
            os.path.join(repo, 'core', 'util.py'): 'util.py',
            os.path.join(repo, 'core', 'main.py'): 'main.py'
        }

        modules = get_modules(self.config, repo)
        self.assertEqual(modules, expected_modules)

    def test_get_modules_no_thermostat(self):
        del self.config['sensor5']

        expected_modules = {
            os.path.join(repo, 'devices', 'ApiTarget.py'): 'ApiTarget.py',
            os.path.join(repo, 'devices', 'Wled.py'): 'Wled.py',
            os.path.join(repo, 'devices', 'TasmotaRelay.py'): 'TasmotaRelay.py',
            os.path.join(repo, 'sensors', 'MotionSensor.py'): 'MotionSensor.py',
            os.path.join(repo, 'sensors', 'Dummy.py'): 'Dummy.py',
            os.path.join(repo, 'devices', 'Device.py'): 'Device.py',
            os.path.join(repo, 'devices', 'DeviceWithLoop.py'): 'DeviceWithLoop.py',
            os.path.join(repo, 'sensors', 'Switch.py'): 'Switch.py',
            os.path.join(repo, 'sensors', 'DesktopTrigger.py'): 'DesktopTrigger.py',
            os.path.join(repo, 'devices', 'Relay.py'): 'Relay.py',
            os.path.join(repo, 'devices', 'Tplink.py'): 'Tplink.py',
            os.path.join(repo, 'devices', 'DesktopTarget.py'): 'DesktopTarget.py',
            os.path.join(repo, 'sensors', 'Sensor.py'): 'Sensor.py',
            os.path.join(repo, 'sensors', 'SensorWithLoop.py'): 'SensorWithLoop.py',
            os.path.join(repo, 'devices', 'LedStrip.py'): 'LedStrip.py',
            os.path.join(repo, 'devices', 'DimmableLight.py'): 'DimmableLight.py',
            os.path.join(repo, 'devices', 'HttpGet.py'): 'HttpGet.py',
            os.path.join(repo, 'devices', 'IrBlaster.py'): 'IrBlaster.py',
            os.path.join(repo, 'core', 'Instance.py'): 'Instance.py',
            os.path.join(repo, 'core', 'Config.py'): 'Config.py',
            os.path.join(repo, 'core', 'Group.py'): 'Group.py',
            os.path.join(repo, 'core', 'SoftwareTimer.py'): 'SoftwareTimer.py',
            os.path.join(repo, 'core', 'app_context.py'): 'app_context.py',
            os.path.join(repo, 'core', 'Api.py'): 'Api.py',
            os.path.join(repo, 'core', 'util.py'): 'util.py',
            os.path.join(repo, 'core', 'main.py'): 'main.py'
        }

        modules = get_modules(self.config, repo)
        self.assertEqual(modules, expected_modules)

    def test_get_modules_realistic(self):
        del self.config['ir_blaster']
        del self.config['sensor3']
        del self.config['sensor4']
        del self.config['sensor5']
        del self.config['device4']
        del self.config['device5']

        expected_modules = {
            os.path.join(repo, 'devices', 'ApiTarget.py'): 'ApiTarget.py',
            os.path.join(repo, 'devices', 'TasmotaRelay.py'): 'TasmotaRelay.py',
            os.path.join(repo, 'sensors', 'MotionSensor.py'): 'MotionSensor.py',
            os.path.join(repo, 'devices', 'Device.py'): 'Device.py',
            os.path.join(repo, 'devices', 'DeviceWithLoop.py'): 'DeviceWithLoop.py',
            os.path.join(repo, 'sensors', 'Switch.py'): 'Switch.py',
            os.path.join(repo, 'devices', 'Tplink.py'): 'Tplink.py',
            os.path.join(repo, 'devices', 'Wled.py'): 'Wled.py',
            os.path.join(repo, 'sensors', 'Sensor.py'): 'Sensor.py',
            os.path.join(repo, 'devices', 'LedStrip.py'): 'LedStrip.py',
            os.path.join(repo, 'devices', 'DimmableLight.py'): 'DimmableLight.py',
            os.path.join(repo, 'devices', 'HttpGet.py'): 'HttpGet.py',
            os.path.join(repo, 'core', 'Instance.py'): 'Instance.py',
            os.path.join(repo, 'core', 'Config.py'): 'Config.py',
            os.path.join(repo, 'core', 'Group.py'): 'Group.py',
            os.path.join(repo, 'core', 'SoftwareTimer.py'): 'SoftwareTimer.py',
            os.path.join(repo, 'core', 'app_context.py'): 'app_context.py',
            os.path.join(repo, 'core', 'Api.py'): 'Api.py',
            os.path.join(repo, 'core', 'util.py'): 'util.py',
            os.path.join(repo, 'core', 'main.py'): 'main.py'
        }

        modules = get_modules(self.config, repo)
        self.assertEqual(modules, expected_modules)


class TestProvisionFunction(TestCase):

    def test_upload_normal(self):
        # Mock Webrepl to return True without doing anything
        with patch.object(Webrepl, 'open_connection', return_value=True), \
             patch.object(Webrepl, 'put_file', return_value=True) as mock_put_file, \
             patch.object(Webrepl, 'put_file_mem', return_value=True) as mock_put_file_mem:

            # Call provision with placeholder values, verify response
            response = provision('192.168.1.123', 'password', {}, {'1': '1', '2': '2', '3': '3'})
            self.assertEqual(response['status'], 200)
            self.assertEqual(response['message'], 'Upload complete.')

            # Verify put_file_mem called once (config file), put_file called once per module
            self.assertEqual(mock_put_file_mem.call_count, 1)
            self.assertEqual(mock_put_file.call_count, 3)

    def test_upload_to_offline_node(self):
        # Mock Webrepl to fail to connect
        with patch.object(Webrepl, 'open_connection', return_value=False):

            # Call provision with placeholder values, verify error
            response = provision('192.168.1.123', 'password', {}, {})
            self.assertEqual(response['status'], 404)
            self.assertEqual(
                response['message'],
                'Error: Unable to connect to node, please make sure it is connected to wifi and try again.'
            )

    def test_upload_connection_timeout(self):
        # Mock Webrepl.put_file to raise TimeoutError
        with patch.object(Webrepl, 'open_connection', return_value=True), \
             patch.object(Webrepl, 'put_file_mem', side_effect=TimeoutError):

            # Call provision with placeholder values, verify error
            response = provision('192.168.1.123', 'password', {}, {})
            self.assertEqual(response['status'], 408)
            self.assertEqual(
                response['message'],
                'Connection timed out - please press target node reset button, wait 30 seconds, and try again.'
            )

    def test_provision_corrupt_filesystem(self):
        # Mock Webrepl.put_file to raise AssertionError for non-library files (simulate failing to upload to root dir)
        with patch.object(Webrepl, 'open_connection', return_value=True), \
             patch.object(Webrepl, 'put_file_mem', side_effect=AssertionError):

            # Call provision with placeholder values, verify error
            response = provision('192.168.1.123', 'password', {}, {})
            self.assertEqual(response['status'], 409)
            self.assertEqual(
                response['message'],
                'Failed due to filesystem error, please re-flash firmware.'
            )
