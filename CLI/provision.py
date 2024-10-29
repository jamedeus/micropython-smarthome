#!/usr/bin/env python3

'''
Upload config file, main.py, and all required modules and libraries to a target
node or IP address in a single step.

Usage
-----

Upload to IP address:
    ./provision.py -c path/to/config.json -ip <target>

Reupload config file to node in cli_config.json
    ./provision.py <friendly-name-from-cli_config.json>

Reupload config files to all nodes in cli_config.json
    Usage: ./provision.py --all
'''

import os
import sys
import json
import argparse
from concurrent.futures import ThreadPoolExecutor
from helper_functions import valid_ip
from provision_tools import get_modules, dependencies, core_modules, provision
from cli_config_manager import CliConfigManager

# Get full paths to repository root directory, CLI tools directory
cli = os.path.dirname(os.path.realpath(__file__))
repo = os.path.split(cli)[0]

# Read cli_config.json from disk
cli_config = CliConfigManager(no_sync='--no-sync' in sys.argv)


def validate_ip(ip):
    '''Validates --ip argument with IPv4 regex'''
    if not valid_ip(ip):
        raise argparse.ArgumentTypeError(f"Invalid IP address '{ip}'")
    return ip


class CustomHelpFormatter(argparse.RawDescriptionHelpFormatter):
    '''Custom help formatter to improve help message for existing node options.

    Prints 2-column help message with node name (can be used as CLI arg) in
    left column, description ("Reupload X to IP") in right.

    Prints standard help message for all other
    '''

    def _format_action(self, action):
        '''Node names: Print 2-column help message with line for each node.
        Other options: Print standard help message
        '''
        if action.dest == "node":
            result = ''
            for node in action.choices:
                ip = cli_config.config['nodes'][node]
                left_column = f'  {node:<22}'
                right_column = f'Reupload {node} to {ip}'
                result += f'{left_column}{right_column}\n'
            return result
        # Use parent class for all other actions
        return super()._format_action(action)


def parse_args():
    '''Parse command line arguments, return parameters used to instantiate
    Provisioner class
    '''
    parser = argparse.ArgumentParser(
        description='''\
Upload config files + dependencies to micropython smarthome nodes

Pick one of the modes listed below (Manual, Node Name, All, Test)
The password flag is optional and works with all modes''',
        usage='%(prog)s [--all | --test <IP> | <node name> | --c /path/to/config.json --ip IP]',
        formatter_class=CustomHelpFormatter
    )

    # Arguments that accept arbitrary IP address and config file path
    manual_group = parser.add_argument_group('Manual')
    manual_group.add_argument(
        '--config',
        metavar='config',
        help='Path to config file'
    )
    manual_group.add_argument(
        '--ip',
        type=validate_ip,
        metavar='IP',
        help='Target IP address'
    )

    # Argument that accepts name of existing node from cli_config.json
    node_group = parser.add_argument_group('Node Name (pick one)')
    node_group.add_argument(
        'node',
        nargs='?',
        choices=cli_config.get_existing_node_names()
    )

    # Argument that reuploads all existing nodes in cli_config.json
    all_group = parser.add_argument_group('All')
    all_group.add_argument(
        '--all',
        action='store_true',
        help='Reupload all nodes from cli_config.json'
    )

    # Argument that uploads unit_test_config.json to specified IP
    test_group = parser.add_argument_group('Test')
    test_group.add_argument(
        '--test',
        type=validate_ip,
        metavar='IP',
        help='Upload unit tests to IP'
    )

    # Argument that accepts string used as webrepl password
    parser.add_argument(
        '--password',
        metavar='<...>',
        help='Webrepl password (uses default if omitted)'
    )

    args = parser.parse_args()

    # If config arg used confirm path is valid
    if bool(args.config):
        # If file not found check if it exists in config_directory
        if not os.path.exists(args.config):
            args.config = cli_config.get_config_filepath(args.config)
            if not os.path.exists(args.config):
                # Throw error if still not found in config directory
                parser.error('Could not find config file')

    # Print error if config arg passed without IP arg
    if bool(args.config) != bool(args.ip):
        parser.print_help()
        parser.error('Must specify both --config and --ip')

    return args, parser


def upload_all(webrepl_password):
    '''Calls upload_node for each node in cli_config.json in separate threads'''

    actions = [(node, webrepl_password, True) for node in cli_config.config['nodes']]
    with ThreadPoolExecutor(max_workers=20) as executor:
        executor.map(upload_node, *zip(*actions))


def upload_node(node, webrepl_password, quiet=False):
    '''Reprovision an existing node from cli_config.json.
    Takes node friendly name and webrepl password.
    Optional quiet arg prevents printing name of each uploaded file.
    '''

    print(f'Uploading {node}...')
    try:
        # Load requested node config from disk
        config = cli_config.load_node_config_file(node)

        # Upload
        result = provision(
            ip=cli_config.config['nodes'][node],
            password=webrepl_password,
            config=config,
            modules=get_modules(config, repo),
            quiet=quiet
        )
        print(f"{node}: {result['message']}")
    except FileNotFoundError:
        print(f'ERROR: {node} config file missing from disk')


def upload_config_to_ip(config_path, ip, webrepl_password):
    '''Takes path to config file, IP address, and webrepl password.
    Uploads config file and all dependencies to target IP.
    '''
    with open(config_path, 'r', encoding='utf-8') as file:
        config = json.load(file)
    result = provision(
        ip=ip,
        password=webrepl_password,
        config=config,
        modules=get_modules(config, repo)
    )
    print(result['message'])

    # Add to cli_config.json if upload successful
    if result['status'] == 200:
        cli_config.add_node(config, ip)


def upload_tests(ip, webrepl_password):
    '''Upload unit tests to IP address passed as arg'''

    # Load unit test config file
    path = os.path.join(repo, 'tests', 'firmware', 'unit_test_config.json')
    with open(path, 'r', encoding='utf-8') as file:
        config = json.load(file)

    # Get list of relative paths for all unit tests
    # (Example: 'tests/firmware/test_core_config.py')
    tests = [i for i in os.listdir(os.path.join(repo, 'tests', 'firmware'))
             if i.startswith('test_')]
    tests = [os.path.join('tests', 'firmware', i) for i in tests]

    # Build list of all device and sensor modules
    modules = []
    for i in dependencies['devices'].values():
        modules.extend(i)
    for i in dependencies['sensors'].values():
        modules.extend(i)
    modules.append('devices/IrBlaster.py')

    # Add unit tests + core modules, remove main.py
    modules.extend(tests)
    modules.extend(core_modules)
    modules.remove('core/main.py')

    # Remove duplicates without changing order
    modules = list(dict.fromkeys(modules))

    # Convert to dict containing pairs of local:remote filesystem paths
    # Local path is uploaded to remote path on target ESP32
    modules = {os.path.join(repo, i): i.split("/")[-1] for i in modules}

    # Add unit_test_main.py (must add after dict comprehension, remote
    # name (main.py) is different than local (unit_test_main.py)
    main_path = os.path.join(repo, 'tests', 'firmware', 'unit_test_main.py')
    modules[main_path] = 'main.py'

    result = provision(ip, webrepl_password, config, modules)
    print(result['message'])


def main():
    '''Parses command line arguments, runs requested actions'''

    args, parser = parse_args()

    # Use configured password if arg omitted
    if args.password:
        webrepl_password = args.password
    else:
        webrepl_password = cli_config.config['webrepl_password']

    # Reprovision all nodes
    if args.all:
        upload_all(webrepl_password)

    # Reprovision specific node
    elif args.node:
        upload_node(args.node, webrepl_password)

    # Upload unit tests
    elif args.test:
        upload_tests(args.test, webrepl_password)

    # Upload given config file to given IP address
    elif args.config and args.ip:
        upload_config_to_ip(args.config, args.ip, webrepl_password)

    else:
        parser.print_help()


if __name__ == "__main__":  # pragma: no cover
    main()
