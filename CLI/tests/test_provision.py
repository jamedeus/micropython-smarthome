import os
import sys
import json
from unittest import TestCase
from unittest.mock import patch, MagicMock, mock_open
from argparse import Namespace, ArgumentParser
from provision import Provisioner, parse_args

# Get full paths to repository root directory, CLI tools directory
cli = os.path.split(os.path.dirname(os.path.realpath(__file__)))[0]
repo = os.path.split(cli)[0]

# Mock nodes.json contents
mock_nodes = {
    "node1": {
        "config": os.path.join(repo, "config", "node1.json"),
        "ip": "192.168.1.123"
    },
    "node2": {
        "config": os.path.join(repo, "config", "node2.json"),
        "ip": "192.168.1.234"
    },
    "node3": {
        "config": os.path.join(repo, "config", "node3.json"),
        "ip": "192.168.1.111"
    },
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
             patch('provision.nodes', mock_nodes):

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

        # Mock provision to do nothing, mock nodes.json, mock open to return empty dict (config file)
        mock_file = mock_open(read_data=json.dumps({}))
        response = {'message': 'Upload complete.', 'status': 200}
        with patch('provision.provision', MagicMock(return_value=response)) as mock_provision, \
             patch('provision.nodes', mock_nodes), \
             patch('builtins.open', mock_file):

            # Instantiate, confirm provision called once for each node
            Provisioner(args, '')
            self.assertEqual(mock_provision.call_count, 3)
            self.assertTrue(mock_provision.called_with('192.168.1.123'))
            self.assertTrue(mock_provision.called_with('192.168.1.234'))
            self.assertTrue(mock_provision.called_with('192.168.1.111'))

    def test_provision_friendly_name(self):
        # Mock args with node friendly name
        args = Namespace(config=None, ip=None, node='node1', all=None, test=None, password=None)

        # Mock provision to do nothing, mock nodes.json, mock open to return empty dict (config file)
        mock_file = mock_open(read_data=json.dumps({}))
        response = {'message': 'Upload complete.', 'status': 200}
        with patch('provision.provision', MagicMock(return_value=response)) as mock_provision, \
             patch('provision.nodes', mock_nodes), \
             patch('builtins.open', mock_file):

            # Instantiate, confirm provision called once with expected IP
            Provisioner(args, '')
            self.assertEqual(mock_provision.call_count, 1)
            self.assertTrue(mock_provision.called_with('192.168.1.123'))

    def test_provision_unit_tests(self):
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
            os.path.join(repo, 'sensors', 'Switch.py'): 'Switch.py',
            os.path.join(repo, 'sensors', 'Desktop_trigger.py'): 'Desktop_trigger.py',
            os.path.join(repo, 'tests', 'test_device_desktop_target.py'): 'test_device_desktop_target.py',
            os.path.join(repo, 'tests', 'test_device_tplink.py'): 'test_device_tplink.py',
            os.path.join(repo, 'tests', 'test_sensor_desktop_trigger.py'): 'test_sensor_desktop_trigger.py',
            os.path.join(repo, 'tests', 'test_sensor_switch.py'): 'test_sensor_switch.py',
            os.path.join(repo, 'tests', 'test_sensor_thermostat.py'): 'test_sensor_thermostat.py',
            os.path.join(repo, 'tests', 'test_device_apitarget.py'): 'test_device_apitarget.py',
            os.path.join(repo, 'tests', 'test_device_wled.py'): 'test_device_wled.py',
            os.path.join(repo, 'tests', 'test_device_dumbrelay.py'): 'test_device_dumbrelay.py',
            os.path.join(repo, 'tests', 'test_core_config.py'): 'test_core_config.py',
            os.path.join(repo, 'tests', 'test_api_api.py'): 'test_api_api.py',
            os.path.join(repo, 'tests', 'test_device_mosfet.py'): 'test_device_mosfet.py',
            os.path.join(repo, 'tests', 'test_device_irblaster.py'): 'test_device_irblaster.py',
            os.path.join(repo, 'tests', 'test_sensor_motionsensor.py'): 'test_sensor_motionsensor.py',
            os.path.join(repo, 'tests', 'test_device_ledstrip.py'): 'test_device_ledstrip.py',
            os.path.join(repo, 'tests', 'test_sensor_dummy.py'): 'test_sensor_dummy.py',
            os.path.join(repo, 'tests', 'test_device_relay.py'): 'test_device_relay.py',
            os.path.join(repo, 'tests', 'test_core_main_loop.py'): 'test_core_main_loop.py',
            os.path.join(repo, 'tests', 'test_core_softwaretimer.py'): 'test_core_softwaretimer.py',
            os.path.join(repo, 'core', 'Config.py'): 'Config.py',
            os.path.join(repo, 'core', 'Group.py'): 'Group.py',
            os.path.join(repo, 'core', 'SoftwareTimer.py'): 'SoftwareTimer.py',
            os.path.join(repo, 'core', 'Api.py'): 'Api.py',
            os.path.join(repo, 'core', 'util.py'): 'util.py',
            os.path.join(repo, 'tests', 'unit_test_main.py'): 'main.py'
        }

        # Mock args to upload unit tests to 192.168.1.123
        args = Namespace(config=None, ip=None, node=None, all=None, test='192.168.1.123', password=None)

        # Mock provision to do nothing, mock nodes.json, mock open to return empty dict (config file)
        mock_file = mock_open(read_data=json.dumps({}))
        response = {'message': 'Upload complete.', 'status': 200}
        with patch('provision.provision', MagicMock(return_value=response)) as mock_provision, \
             patch('provision.nodes', mock_nodes), \
             patch('builtins.open', mock_file):

            # Instantiate, confirm called once with given IP + test modules
            Provisioner(args, '')
            self.assertTrue(mock_provision.called_with('192.168.1.123'))
            self.assertTrue(mock_provision.called_with(test_modules))
            self.assertTrue(mock_provision.called_once)

    def test_provision_manual_args(self):
        # Mock args with manually specified config file, IP, password
        args = Namespace(
            config='../config/node1.json',
            ip='192.168.1.123',
            node=None,
            all=None,
            test=None,
            password='hunter2'
        )

        # Mock provision to do nothing, mock nodes.json, mock open + json.load to return empty dict (config)
        mock_file = mock_open(read_data=json.dumps({}))
        response = {'message': 'Upload complete.', 'status': 200}
        with patch('provision.provision', MagicMock(return_value=response)) as mock_provision, \
             patch('provision.json.load', MagicMock(return_value={})), \
             patch('provision.nodes', mock_nodes), \
             patch('builtins.open', mock_file):

            # Instantiate, confirm provision called once with expected IP and password
            Provisioner(args, '')
            self.assertEqual(mock_provision.call_count, 1)
            self.assertTrue(mock_provision.called_with('192.168.1.123'))
            self.assertTrue(mock_provision.called_with('hunter2'))

    def test_provision_no_args(self):
        # Mock args, all blank
        args = Namespace(config=None, ip=None, node=None, all=None, test=None, password=None)

        # Mock parser object
        mock_parser = MagicMock(spec=ArgumentParser)

        # Instantiate with mock args and parser, confirm print_help called
        Provisioner(args, mock_parser)
        self.assertTrue(mock_parser.print_help.called)
