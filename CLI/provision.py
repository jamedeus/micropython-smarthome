#!/usr/bin/env python3

# Upload config file + main.py + all required modules and libraries in a single step

# Usage: ./provision.py -c path/to/config.json -ip <target>
# Usage: ./provision.py <friendly-name-from-nodes.json>
# Usage: ./provision.py --all

import os
import json
import argparse
from Webrepl import Webrepl
from helper_functions import valid_ip, is_device, is_sensor

# Dependency relative paths for all device and sensor types, used by get_modules
dependencies = {
    'devices': {
        'dimmer': ["devices/Tplink.py", "devices/Device.py", "devices/DimmableLight.py"],
        'bulb': ["devices/Tplink.py", "devices/Device.py", "devices/DimmableLight.py"],
        'relay': ["devices/Relay.py", "devices/Device.py"],
        'dumb-relay': ["devices/DumbRelay.py", "devices/Device.py"],
        'desktop': ["devices/Desktop_target.py", "devices/Device.py"],
        'pwm': ["devices/LedStrip.py", "devices/Device.py", "devices/DimmableLight.py"],
        'mosfet': ["devices/Mosfet.py", "devices/Device.py"],
        'api-target': ["devices/ApiTarget.py", "devices/Device.py"],
        'wled': ["devices/Wled.py", "devices/Device.py", "devices/DimmableLight.py"]
    },
    'sensors': {
        'pir': ["sensors/MotionSensor.py", "sensors/Sensor.py"],
        'si7021': ["sensors/Thermostat.py", "sensors/Sensor.py"],
        'dummy': ["sensors/Dummy.py", "sensors/Sensor.py"],
        'switch': ["sensors/Switch.py", "sensors/Sensor.py"],
        'desktop': ["sensors/Desktop_trigger.py", "sensors/Sensor.py"],
    }
}


class Provisioner():
    def __init__(self):
        # Get full paths to repository root directory, CLI tools directory
        self.cli = os.path.dirname(os.path.realpath(__file__))
        self.repo = os.path.split(self.cli)[0]

        # Load CLI config file
        try:
            with open(os.path.join(self.cli, 'nodes.json'), 'r') as file:
                self.nodes = json.load(file)
        except FileNotFoundError:
            print("Warning: Unable to find nodes.json, friendly names will not work")
            self.nodes = {}

        # Validate CLI arguments
        args = self.parse_args()

        # Use default password if arg omitted
        if args.password:
            self.passwd = args.password
        else:
            self.passwd = "password"

        # Reprovision all nodes
        if args.all:
            # Iterate all nodes in config file
            for i in self.nodes:
                print(f"\n{i}\n")

                # Load config from disk
                with open(self.nodes[i]["config"], 'r') as file:
                    config = json.load(file)

                # Get modules
                modules = self.get_modules(config)

                # Upload
                self.provision(self.nodes[i]["ip"], self.passwd, config, modules)

        # Reprovision specific node
        elif args.node:
            # Load requested node config from disk
            with open(self.nodes[args.node]["config"], 'r') as file:
                config = json.load(file)

            # Get modules, upload
            modules = self.get_modules((config))
            self.provision(self.nodes[args.node]["ip"], self.passwd, config, modules)

        # Upload unit tests to IP address
        # TODO broken, doesn't upload unit_test_main.py as main.py
        elif args.test:
            # Load unit test config file
            with open(os.path.join(self.repo, "tests", "unit_test_config.json"), 'r') as file:
                config = json.load(file)

            # Build list of all device and sensor classes
            modules = []
            for device in dependencies['devices']:
                modules.extend(dependencies['devices'][device])
            for sensor in dependencies['sensors']:
                modules.extend(dependencies['sensors'][sensor])

            # Add all unit test files
            for i in os.listdir(os.path.join(self.repo, 'tests')):
                if i.startswith('test_'):
                    modules.append(os.path.join('tests', i))

            # Add IR codes
            modules.append(os.path.join('lib', 'samsung-codes.json'))
            modules.append(os.path.join('lib', 'whynter-codes.json'))

            # Remove duplicates
            modules = set(modules)

            # Convert to dict containing pairs of local:remote filesystem paths
            # Local path is uploaded to remote path on target ESP32
            modules = {os.path.join(self.repo, i): i.split("/")[1] for i in modules}

            self.provision(args.test, self.passwd, config, modules)

        # Upload given config file to given IP address
        elif args.config and args.ip:
            config = json.load(args.config)
            modules = self.get_modules(config)
            self.provision(args.ip, self.passwd, config, modules)

        else:
            self.parser.print_help()

    def parse_args(self):
        self.parser = argparse.ArgumentParser(
            description='''\
Upload config files + dependencies to micropython smarthome nodes

Pick one of the modes listed below (Manual, Node Name, All, Test)
The password flag is optional and works with all modes''',
            usage='%(prog)s [--all | --test <IP> | <node name> | --c /path/to/config.json --ip IP]',
            formatter_class=argparse.RawDescriptionHelpFormatter
        )

        manual_group = self.parser.add_argument_group('Manual')
        manual_group.add_argument('--config', type=argparse.FileType('r'), metavar='config', help='Path to config file')
        manual_group.add_argument('--ip', type=self.validate_ip, metavar='IP', help='Target IP address')

        node_group = self.parser.add_argument_group('Node Name (pick one)')
        node_group.add_argument('node', nargs='?', choices=self.nodes.keys())

        all_group = self.parser.add_argument_group('All')
        all_group.add_argument('--all', action='store_true', help='Reupload all nodes from nodes.json')

        test_group = self.parser.add_argument_group('Test')
        test_group.add_argument('--test', type=self.validate_ip, metavar='IP', help='Upload unit tests to IP')

        self.parser.add_argument('--password', metavar='<...>', help='Webrepl password (uses default if omitted)')

        args = self.parser.parse_args()
        if bool(args.config) != bool(args.ip):
            self.parser.error('Must specify both --config and --ip')

        return args

    def validate_ip(self, ip):
        if not valid_ip(ip):
            raise argparse.ArgumentTypeError(f"Invalid IP address '{ip}'")
        return ip

    # Takes IP, password, loaded config file, dict of modules
    # Uploads all modules
    def provision(self, ip, password, config, modules):
        node = Webrepl(ip, password)
        if not node.open_connection():
            print(f"Error: {ip} not connected to network or not accepting webrepl connections.\n")
            return

        # Upload all device/sensor modules
        for local, remote in modules.items():
            print(f"{local} -> {ip}:/{remote}")
            node.put_file(local, remote)
            print()

        # Upload config file
        node.put_file_mem(config, "config.json")

        # Upload core dependencies (must upload main.py last, triggers reboot)
        for core in ["Config.py", "Group.py", "SoftwareTimer.py", "Api.py", "util.py", "main.py"]:
            local = os.path.join(self.repo, "core", core)
            print(f"{local} -> {ip}:/{core}")
            node.put_file(local, core)
            print()

        node.close_connection()

    # Takes full config file, returns list of classes for each device and sensor type
    def get_modules(self, config):
        modules = []

        # Get lists of device and sensor types
        device_types = [config[device]['_type'] for device in config.keys() if is_device(device)]
        sensor_types = [config[sensor]['_type'] for sensor in config.keys() if is_sensor(sensor)]

        # Get dependencies for all device and sensor types
        for dtype in device_types:
            modules.extend(dependencies['devices'][dtype])
        for stype in sensor_types:
            modules.extend(dependencies['sensors'][stype])

        # Remove duplicates
        modules = set(modules)

        # Convert to dict containing pairs of local:remote filesystem paths
        # Local path is uploaded to remote path on target ESP32
        modules = {os.path.join(self.repo, i): i.split("/")[1] for i in modules}

        return modules


if __name__ == "__main__":
    # Create instance, pass CLI arguments to init
    Provisioner()
