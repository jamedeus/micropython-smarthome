import os
import sys
import json
from unittest import TestCase
from unittest.mock import patch, MagicMock, mock_open
from argparse import Namespace, ArgumentParser
from provision import Provisioner, parse_args
from provision_tools import provision, get_modules
from Webrepl import Webrepl

# Get full paths to repository root directory, CLI tools directory
cli = os.path.split(os.path.dirname(os.path.realpath(__file__)))[0]
repo = os.path.split(cli)[0]

# Mock cli_config.json contents
mock_cli_config = {
    'nodes': {
        "node1": {
            "config": os.path.join(repo, "config_files", "node1.json"),
            "ip": "192.168.1.123"
        },
        "node2": {
            "config": os.path.join(repo, "config_files", "node2.json"),
            "ip": "192.168.1.234"
        },
        "node3": {
            "config": os.path.join(repo, "config_files", "node3.json"),
            "ip": "192.168.1.111"
        },
    },
    'webrepl_password': 'password',
    'config_directory': os.path.join(repo, 'config_files')
}


class TestArgParser(TestCase):

    def test_all(self):
        with patch.object(sys, 'argv', ['', '--all']):
            args, parser = parse_args()

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
            args, parser = parse_args()

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
        with patch.object(sys, 'argv', ['', 'node1']), \
             patch('provision.cli_config', mock_cli_config):

            args, parser = parse_args()

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
        mock_file = mock_open(read_data=json.dumps({}))
        cli_args = ['', '--config', '../config/node1.json', '--ip', '192.168.1.123', '--password', 'hunter2']
        with patch.object(sys, 'argv', cli_args), \
             patch('builtins.open', mock_file):
            args, parser = parse_args()

        # Confirm parameters matched to correct args
        self.assertEqual(args.config.read(), json.dumps({}))
        self.assertEqual(args.ip, '192.168.1.123')
        self.assertEqual(args.password, 'hunter2')

        # Confirm all other args empty
        self.assertFalse(args.all)
        self.assertFalse(args.test)
        self.assertFalse(args.node)

    def test_invalid_ip(self):
        mock_file = mock_open(read_data=json.dumps({}))
        with patch.object(sys, 'argv', ['', '--config', '../config/node1.json', '--ip', '192.168.1']), \
             patch('builtins.open', mock_file), \
             self.assertRaises(SystemExit):

            parse_args()

    def test_missing_config_file(self):
        mock_file = mock_open(read_data=json.dumps({}))
        with patch.object(sys, 'argv', ['', '--ip', '192.168.1.123']), \
             patch('builtins.open', mock_file), \
             self.assertRaises(SystemExit):

            parse_args()


class TestInstantiation(TestCase):

    def test_provision_all(self):
        # Mock args for --all
        args = Namespace(config=None, ip=None, node=None, all=True, test=None, password=None)

        # Mock provision to do nothing, mock cli_config.json, mock open to return empty dict (config file)
        mock_file = mock_open(read_data=json.dumps({}))
        response = {'message': 'Upload complete.', 'status': 200}
        with patch('provision.provision', MagicMock(return_value=response)) as mock_provision, \
             patch('provision.cli_config', mock_cli_config), \
             patch('builtins.open', mock_file):

            # Instantiate, confirm provision called once for each node
            Provisioner(args, '')
            self.assertEqual(mock_provision.call_count, 3)

            self.assertEqual(mock_provision.call_args_list[0][0][0], '192.168.1.123')
            self.assertEqual(mock_provision.call_args_list[1][0][0], '192.168.1.234')
            self.assertEqual(mock_provision.call_args_list[2][0][0], '192.168.1.111')

    def test_provision_friendly_name(self):
        # Mock args with node friendly name
        args = Namespace(config=None, ip=None, node='node1', all=None, test=None, password=None)

        # Mock provision to do nothing, mock cli_config.json, mock open to return empty dict (config file)
        mock_file = mock_open(read_data=json.dumps({}))
        response = {'message': 'Upload complete.', 'status': 200}
        with patch('provision.provision', MagicMock(return_value=response)) as mock_provision, \
             patch('provision.cli_config', mock_cli_config), \
             patch('builtins.open', mock_file):

            # Instantiate, confirm provision called once with expected IP
            Provisioner(args, '')
            self.assertEqual(mock_provision.call_count, 1)
            self.assertEqual(mock_provision.call_args[0][0], '192.168.1.123')

    def test_provision_unit_tests(self):
        self.maxDiff = None
        # Expected test modules
        test_modules = {
            os.path.join(repo, 'devices', 'Tplink.py'): 'Tplink.py',
            os.path.join(repo, 'devices', 'Device.py'): 'Device.py',
            os.path.join(repo, 'devices', 'DimmableLight.py'): 'DimmableLight.py',
            os.path.join(repo, 'devices', 'Relay.py'): 'Relay.py',
            os.path.join(repo, 'devices', 'DumbRelay.py'): 'DumbRelay.py',
            os.path.join(repo, 'devices', 'Desktop_target.py'): 'Desktop_target.py',
            os.path.join(repo, 'devices', 'LedStrip.py'): 'LedStrip.py',
            os.path.join(repo, 'devices', 'Mosfet.py'): 'Mosfet.py',
            os.path.join(repo, 'devices', 'ApiTarget.py'): 'ApiTarget.py',
            os.path.join(repo, 'devices', 'Wled.py'): 'Wled.py',
            os.path.join(repo, 'sensors', 'MotionSensor.py'): 'MotionSensor.py',
            os.path.join(repo, 'sensors', 'Sensor.py'): 'Sensor.py',
            os.path.join(repo, 'sensors', 'Thermostat.py'): 'Thermostat.py',
            os.path.join(repo, 'sensors', 'Dummy.py'): 'Dummy.py',
            os.path.join(repo, 'sensors', 'LoadCell.py'): 'LoadCell.py',
            os.path.join(repo, 'sensors', 'Switch.py'): 'Switch.py',
            os.path.join(repo, 'sensors', 'Desktop_trigger.py'): 'Desktop_trigger.py',
            os.path.join(repo, 'devices', 'IrBlaster.py'): 'IrBlaster.py',
            os.path.join(repo, 'tests', 'firmware', 'test_device_desktop_target.py'): 'test_device_desktop_target.py',
            os.path.join(repo, 'tests', 'firmware', 'test_device_device.py'): 'test_device_device.py',
            os.path.join(repo, 'tests', 'firmware', 'test_device_dimmablelight.py'): 'test_device_dimmablelight.py',
            os.path.join(repo, 'tests', 'firmware', 'test_device_tplink.py'): 'test_device_tplink.py',
            os.path.join(repo, 'tests', 'firmware', 'test_sensor_desktop_trigger.py'): 'test_sensor_desktop_trigger.py',
            os.path.join(repo, 'tests', 'firmware', 'test_sensor_switch.py'): 'test_sensor_switch.py',
            os.path.join(repo, 'tests', 'firmware', 'test_sensor_sensor.py'): 'test_sensor_sensor.py',
            os.path.join(repo, 'tests', 'firmware', 'test_sensor_thermostat.py'): 'test_sensor_thermostat.py',
            os.path.join(repo, 'tests', 'firmware', 'test_device_apitarget.py'): 'test_device_apitarget.py',
            os.path.join(repo, 'tests', 'firmware', 'test_device_wled.py'): 'test_device_wled.py',
            os.path.join(repo, 'tests', 'firmware', 'test_device_dumbrelay.py'): 'test_device_dumbrelay.py',
            os.path.join(repo, 'tests', 'firmware', 'test_core_config.py'): 'test_core_config.py',
            os.path.join(repo, 'tests', 'firmware', 'test_api_api.py'): 'test_api_api.py',
            os.path.join(repo, 'tests', 'firmware', 'test_device_mosfet.py'): 'test_device_mosfet.py',
            os.path.join(repo, 'tests', 'firmware', 'test_device_irblaster.py'): 'test_device_irblaster.py',
            os.path.join(repo, 'tests', 'firmware', 'test_sensor_motionsensor.py'): 'test_sensor_motionsensor.py',
            os.path.join(repo, 'tests', 'firmware', 'test_device_ledstrip.py'): 'test_device_ledstrip.py',
            os.path.join(repo, 'tests', 'firmware', 'test_sensor_dummy.py'): 'test_sensor_dummy.py',
            os.path.join(repo, 'tests', 'firmware', 'test_sensor_load_cell.py'): 'test_sensor_load_cell.py',
            os.path.join(repo, 'tests', 'firmware', 'test_device_relay.py'): 'test_device_relay.py',
            os.path.join(repo, 'tests', 'firmware', 'test_core_main.py'): 'test_core_main.py',
            os.path.join(repo, 'tests', 'firmware', 'test_core_softwaretimer.py'): 'test_core_softwaretimer.py',
            os.path.join(repo, 'tests', 'firmware', 'test_core_util.py'): 'test_core_util.py',
            os.path.join(repo, 'tests', 'firmware', 'test_core_group.py'): 'test_core_group.py',
            os.path.join(repo, 'tests', 'firmware', 'test_core_wifi_setup.py'): 'test_core_wifi_setup.py',
            os.path.join(repo, 'core', 'Instance.py'): 'Instance.py',
            os.path.join(repo, 'core', 'Config.py'): 'Config.py',
            os.path.join(repo, 'core', 'Group.py'): 'Group.py',
            os.path.join(repo, 'core', 'SoftwareTimer.py'): 'SoftwareTimer.py',
            os.path.join(repo, 'core', 'Api.py'): 'Api.py',
            os.path.join(repo, 'core', 'util.py'): 'util.py',
            os.path.join(repo, 'tests', 'firmware', 'unit_test_main.py'): 'main.py'
        }

        # Mock args to upload unit tests to 192.168.1.123
        args = Namespace(config=None, ip=None, node=None, all=None, test='192.168.1.123', password=None)

        # Mock provision to do nothing, mock cli_config.json, mock open to return empty dict (config file)
        mock_file = mock_open(read_data=json.dumps({}))
        response = {'message': 'Upload complete.', 'status': 200}
        with patch('provision.provision', MagicMock(return_value=response)) as mock_provision, \
             patch('provision.cli_config', mock_cli_config), \
             patch('builtins.open', mock_file):

            # Instantiate, confirm called once with given IP + test modules
            Provisioner(args, '')
            args = mock_provision.call_args[0]
            self.assertEqual(args[0], '192.168.1.123')
            self.assertEqual(args[3], test_modules)
            self.assertTrue(mock_provision.called_once)

    def test_provision_manual_args(self):
        # Mock config file contents with ID parameter set (used as key in cli_config.json nodes section)
        mock_file_contents = {'metadata': {'id': 'Node4'}}

        # Mock file object to simulate config arg
        mock_file = mock_open(read_data=json.dumps(mock_file_contents))
        mock_file.name = '../config/node4.json'

        # Mock args with manually specified config file, IP, password
        args = Namespace(
            config=mock_file,
            ip='192.168.1.123',
            node=None,
            all=None,
            test=None,
            password='hunter2'
        )

        # Confirm ID from mock config not in cli_config.json nodes section
        self.assertNotIn('node4', mock_cli_config['nodes'].keys())

        # Mock provision to do nothing, mock cli_config.json, mock open + json.load to return empty dict (config)
        response = {'message': 'Upload complete.', 'status': 200}
        with patch('provision.provision', MagicMock(return_value=response)) as mock_provision, \
             patch('provision.json.load', MagicMock(return_value=mock_file_contents)), \
             patch('helper_functions.get_cli_config', return_value=mock_cli_config), \
             patch('provision.cli_config', mock_cli_config), \
             patch('builtins.open', mock_file):

            # Instantiate, confirm provision called once with expected IP, password, config
            Provisioner(args, '')
            self.assertEqual(mock_provision.call_count, 1)
            args = mock_provision.call_args[0]
            self.assertEqual(args[0], '192.168.1.123')
            self.assertEqual(args[1], 'hunter2')
            self.assertEqual(args[2], mock_file_contents)

        # Confirm ID from mock config was added to cli_config.json nodes section
        self.assertIn('node4', mock_cli_config['nodes'].keys())
        self.assertEqual(mock_cli_config['nodes']['node4']['ip'], '192.168.1.123')
        self.assertEqual(mock_cli_config['nodes']['node4']['config'], os.path.abspath('../config/node4.json'))

    def test_provision_no_args(self):
        # Mock args, all blank
        args = Namespace(config=None, ip=None, node=None, all=None, test=None, password=None)

        # Mock parser object
        mock_parser = MagicMock(spec=ArgumentParser)

        # Instantiate with mock args and parser, confirm print_help called
        Provisioner(args, mock_parser)
        self.assertTrue(mock_parser.print_help.called)


class TestGetModules(TestCase):
    def setUp(self):
        with open(os.path.join(repo, "tests", "cli", "unit-test-config.json"), 'r') as file:
            self.config = json.load(file)

    def test_get_modules_full_config(self):

        expected_modules = {
            os.path.join(repo, 'devices', 'ApiTarget.py'): 'ApiTarget.py',
            os.path.join(repo, 'devices', 'Wled.py'): 'Wled.py',
            os.path.join(repo, 'devices', 'Mosfet.py'): 'Mosfet.py',
            os.path.join(repo, 'devices', 'Relay.py'): 'Relay.py',
            os.path.join(repo, 'sensors', 'MotionSensor.py'): 'MotionSensor.py',
            os.path.join(repo, 'sensors', 'Dummy.py'): 'Dummy.py',
            os.path.join(repo, 'devices', 'Device.py'): 'Device.py',
            os.path.join(repo, 'sensors', 'Switch.py'): 'Switch.py',
            os.path.join(repo, 'sensors', 'Desktop_trigger.py'): 'Desktop_trigger.py',
            os.path.join(repo, 'devices', 'DumbRelay.py'): 'DumbRelay.py',
            os.path.join(repo, 'devices', 'Tplink.py'): 'Tplink.py',
            os.path.join(repo, 'devices', 'Desktop_target.py'): 'Desktop_target.py',
            os.path.join(repo, 'sensors', 'Thermostat.py'): 'Thermostat.py',
            os.path.join(repo, 'sensors', 'Sensor.py'): 'Sensor.py',
            os.path.join(repo, 'devices', 'LedStrip.py'): 'LedStrip.py',
            os.path.join(repo, 'devices', 'DimmableLight.py'): 'DimmableLight.py',
            os.path.join(repo, 'devices', 'IrBlaster.py'): 'IrBlaster.py',
            os.path.join(repo, 'core', 'Instance.py'): 'Instance.py',
            os.path.join(repo, 'core', 'Config.py'): 'Config.py',
            os.path.join(repo, 'core', 'Group.py'): 'Group.py',
            os.path.join(repo, 'core', 'SoftwareTimer.py'): 'SoftwareTimer.py',
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
            os.path.join(repo, 'devices', 'Mosfet.py'): 'Mosfet.py',
            os.path.join(repo, 'devices', 'Relay.py'): 'Relay.py',
            os.path.join(repo, 'sensors', 'MotionSensor.py'): 'MotionSensor.py',
            os.path.join(repo, 'sensors', 'Dummy.py'): 'Dummy.py',
            os.path.join(repo, 'devices', 'Device.py'): 'Device.py',
            os.path.join(repo, 'sensors', 'Switch.py'): 'Switch.py',
            os.path.join(repo, 'sensors', 'Desktop_trigger.py'): 'Desktop_trigger.py',
            os.path.join(repo, 'devices', 'DumbRelay.py'): 'DumbRelay.py',
            os.path.join(repo, 'devices', 'Tplink.py'): 'Tplink.py',
            os.path.join(repo, 'devices', 'Desktop_target.py'): 'Desktop_target.py',
            os.path.join(repo, 'sensors', 'Thermostat.py'): 'Thermostat.py',
            os.path.join(repo, 'sensors', 'Sensor.py'): 'Sensor.py',
            os.path.join(repo, 'devices', 'LedStrip.py'): 'LedStrip.py',
            os.path.join(repo, 'devices', 'DimmableLight.py'): 'DimmableLight.py',
            os.path.join(repo, 'core', 'Instance.py'): 'Instance.py',
            os.path.join(repo, 'core', 'Config.py'): 'Config.py',
            os.path.join(repo, 'core', 'Group.py'): 'Group.py',
            os.path.join(repo, 'core', 'SoftwareTimer.py'): 'SoftwareTimer.py',
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
            os.path.join(repo, 'devices', 'Mosfet.py'): 'Mosfet.py',
            os.path.join(repo, 'devices', 'Relay.py'): 'Relay.py',
            os.path.join(repo, 'sensors', 'MotionSensor.py'): 'MotionSensor.py',
            os.path.join(repo, 'sensors', 'Dummy.py'): 'Dummy.py',
            os.path.join(repo, 'devices', 'Device.py'): 'Device.py',
            os.path.join(repo, 'sensors', 'Switch.py'): 'Switch.py',
            os.path.join(repo, 'sensors', 'Desktop_trigger.py'): 'Desktop_trigger.py',
            os.path.join(repo, 'devices', 'DumbRelay.py'): 'DumbRelay.py',
            os.path.join(repo, 'devices', 'Tplink.py'): 'Tplink.py',
            os.path.join(repo, 'devices', 'Desktop_target.py'): 'Desktop_target.py',
            os.path.join(repo, 'sensors', 'Sensor.py'): 'Sensor.py',
            os.path.join(repo, 'devices', 'LedStrip.py'): 'LedStrip.py',
            os.path.join(repo, 'devices', 'DimmableLight.py'): 'DimmableLight.py',
            os.path.join(repo, 'devices', 'IrBlaster.py'): 'IrBlaster.py',
            os.path.join(repo, 'core', 'Instance.py'): 'Instance.py',
            os.path.join(repo, 'core', 'Config.py'): 'Config.py',
            os.path.join(repo, 'core', 'Group.py'): 'Group.py',
            os.path.join(repo, 'core', 'SoftwareTimer.py'): 'SoftwareTimer.py',
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
        del self.config['device7']

        expected_modules = {
            os.path.join(repo, 'devices', 'ApiTarget.py'): 'ApiTarget.py',
            os.path.join(repo, 'devices', 'Relay.py'): 'Relay.py',
            os.path.join(repo, 'sensors', 'MotionSensor.py'): 'MotionSensor.py',
            os.path.join(repo, 'devices', 'Device.py'): 'Device.py',
            os.path.join(repo, 'sensors', 'Switch.py'): 'Switch.py',
            os.path.join(repo, 'devices', 'Tplink.py'): 'Tplink.py',
            os.path.join(repo, 'devices', 'Wled.py'): 'Wled.py',
            os.path.join(repo, 'sensors', 'Sensor.py'): 'Sensor.py',
            os.path.join(repo, 'devices', 'LedStrip.py'): 'LedStrip.py',
            os.path.join(repo, 'devices', 'DimmableLight.py'): 'DimmableLight.py',
            os.path.join(repo, 'core', 'Instance.py'): 'Instance.py',
            os.path.join(repo, 'core', 'Config.py'): 'Config.py',
            os.path.join(repo, 'core', 'Group.py'): 'Group.py',
            os.path.join(repo, 'core', 'SoftwareTimer.py'): 'SoftwareTimer.py',
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
