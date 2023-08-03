#!/usr/bin/env python3

# Upload config file + main.py + all required modules and libraries in a single step

# Usage: ./provision.py -c path/to/config.json -ip <target>
# Usage: ./provision.py <friendly-name-from-nodes.json>
# Usage: ./provision.py --all

import os
import json
import argparse
from helper_functions import valid_ip
from provision_tools import get_modules, dependencies, core_modules, provision


# Get full paths to repository root directory, CLI tools directory
cli = os.path.dirname(os.path.realpath(__file__))
repo = os.path.split(cli)[0]

# Load CLI config file
try:
    with open(os.path.join(cli, 'nodes.json'), 'r') as file:
        nodes = json.load(file)
except FileNotFoundError:
    print("Warning: Unable to find nodes.json, friendly names will not work")
    nodes = {}


def validate_ip(ip):
    if not valid_ip(ip):
        raise argparse.ArgumentTypeError(f"Invalid IP address '{ip}'")
    return ip


def parse_args():
    parser = argparse.ArgumentParser(
        description='''\
Upload config files + dependencies to micropython smarthome nodes

Pick one of the modes listed below (Manual, Node Name, All, Test)
The password flag is optional and works with all modes''',
        usage='%(prog)s [--all | --test <IP> | <node name> | --c /path/to/config.json --ip IP]',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    manual_group = parser.add_argument_group('Manual')
    manual_group.add_argument('--config', type=argparse.FileType('r'), metavar='config', help='Path to config file')
    manual_group.add_argument('--ip', type=validate_ip, metavar='IP', help='Target IP address')

    node_group = parser.add_argument_group('Node Name (pick one)')
    node_group.add_argument('node', nargs='?', choices=nodes.keys())

    all_group = parser.add_argument_group('All')
    all_group.add_argument('--all', action='store_true', help='Reupload all nodes from nodes.json')

    test_group = parser.add_argument_group('Test')
    test_group.add_argument('--test', type=validate_ip, metavar='IP', help='Upload unit tests to IP')

    parser.add_argument('--password', metavar='<...>', help='Webrepl password (uses default if omitted)')

    args = parser.parse_args()
    if bool(args.config) != bool(args.ip):
        parser.print_help()
        parser.error('Must specify both --config and --ip')

    return args, parser


class Provisioner():
    def __init__(self, args, parser):
        # Use default password if arg omitted
        if args.password:
            self.passwd = args.password
        else:
            self.passwd = "password"

        # Reprovision all nodes
        if args.all:
            self.upload_all()

        # Reprovision specific node
        elif args.node:
            self.upload_node(args.node)

        # Upload unit tests
        elif args.test:
            self.upload_tests(args.test)

        # Upload given config file to given IP address
        elif args.config and args.ip:
            config = json.load(args.config)
            modules = get_modules(config, repo)
            result = provision(args.ip, self.passwd, config, modules)
            print(result['message'])

            # Add to nodes.json if upload successful
            if result['status'] == 200:
                self.add_to_nodes(config['metadata']['id'], args.config.name, args.ip)

        else:
            parser.print_help()

    # Add new node to nodes.json after successful upload
    # Takes friendly name, config rel/abs path, ip address
    def add_to_nodes(self, friendly_name, config_path, ip):
        if friendly_name not in nodes.keys():
            nodes[friendly_name] = {
                'config': os.path.abspath(config_path),
                'ip': ip
            }
            with open(os.path.join(cli, 'nodes.json'), 'w') as file:
                json.dump(nodes, file)

    # Iterate nodes.json, reprovision all nodes
    def upload_all(self):
        # Iterate all nodes in config file
        for i in nodes:
            print(f"\n{i}\n")

            # Load config from disk
            with open(nodes[i]["config"], 'r') as file:
                config = json.load(file)

            # Get modules
            modules = get_modules(config, repo)

            # Upload
            result = provision(nodes[i]["ip"], self.passwd, config, modules)
            print(result['message'])

    # Reprovision an existing node, accepts friendly name as arg
    def upload_node(self, node):
        # Load requested node config from disk
        with open(nodes[node]["config"], 'r') as file:
            config = json.load(file)

        # Get modules, upload
        modules = get_modules(config, repo)
        result = provision(nodes[node]["ip"], self.passwd, config, modules)
        print(result['message'])

    # Upload unit tests to IP address
    def upload_tests(self, ip):
        # Load unit test config file
        with open(os.path.join(repo, "tests", 'firmware', "unit_test_config.json"), 'r') as file:
            config = json.load(file)

        # Get list of relative paths for all unit tests (Example: 'tests/firmware/test_core_config.py')
        tests = [i for i in os.listdir(os.path.join(repo, 'tests', 'firmware')) if i.startswith('test_')]
        tests = [os.path.join('tests', 'firmware', i) for i in tests]

        # Build list of all device and sensor modules
        modules = []
        [modules.extend(i) for i in dependencies['devices'].values()]
        [modules.extend(i) for i in dependencies['sensors'].values()]

        # Add unit tests + core modules, remove main.py
        modules.extend(tests)
        modules.extend(core_modules)
        modules.pop()

        # Remove duplicates without changing order
        modules = list(dict.fromkeys(modules))

        # Convert to dict containing pairs of local:remote filesystem paths
        # Local path is uploaded to remote path on target ESP32
        modules = {os.path.join(repo, i): i.split("/")[-1] for i in modules}

        # Add unit_test_main.py (must add after dict comprehension, remote name is different)
        modules[os.path.join(repo, 'tests', 'firmware', 'unit_test_main.py')] = 'main.py'

        result = provision(ip, self.passwd, config, modules)
        print(result['message'])


if __name__ == "__main__":
    # Instantiate with validated CLI args
    Provisioner(*parse_args())
