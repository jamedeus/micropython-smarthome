#!/usr/bin/env python3

'''Main CLI script'''

import os
import json
import requests
import questionary
from helper_functions import (
    valid_ip,
    valid_uri,
    get_cli_config,
    write_cli_config,
    save_node_config_file,
    get_config_filepath,
    remove_node_from_cli_config
)
from config_generator import GenerateConfigFile
from provision import upload_node, upload_config_to_ip
from api_client import example_usage, parse_command


# Read cli_config.json from disk
cli_config = get_cli_config()


def sync_cli_config():
    '''Updates cli_config.json with values from django database'''

    # Request dict of existing nodes from backend
    response = requests.get(
        f'{cli_config["django_backend"]}/get_nodes',
        timeout=5
    )
    if response.status_code == 200:
        # Merge response dict into cli_config with union operator
        cli_config['nodes'] |= response.json()['message']
    else:
        print('Failed to sync nodes')

    # Request dict of existing schedule keywords from backend
    response = requests.get(
        f'{cli_config["django_backend"]}/get_schedule_keywords',
        timeout=5
    )
    if response.status_code == 200:
        # Merge response dict into cli_config with union operator
        cli_config['schedule_keywords'] |= response.json()['message']
    else:
        print('Failed to sync keywords')

    write_cli_config(cli_config)
    return cli_config


def download_all_node_config_files():
    '''Iterates nodes in cli_config.json, downloads each config file from
    backend and writes to config_dir (set in cli_config.json).
    '''
    for node, ip in cli_config['nodes'].items():
        config = download_node_config_file(ip)
        if config:
            # Create JSON config file in config_directory
            save_node_config_file(config)
            print(f'Downloaded {node} config file')

        else:
            print(f'Failed to download {node} config file')


def download_node_config_file(ip):
    '''Takes node IP, requests config file from backend and returns'''
    response = requests.get(
        f'{cli_config["django_backend"]}/get_node_config/{ip}',
        timeout=5
    )
    if response.status_code == 200:
        return response.json()['message']
    return False


def set_django_address(address):
    '''Takes URI, writes to cli_config.json django_backend key.'''
    cli_config['django_backend'] = address
    write_cli_config(cli_config)


def sync_prompt():
    '''Prompt allows user to configure django server to sync from, update
    cli_config.json from django database, or download config files from django.
    '''
    while True:
        choice = questionary.select(
            "\nWhat would you like to do?",
            choices=[
                "Set django address",
                "Sync current nodes from django",
                "Download all config files from django",
                "Done"
            ]
        ).unsafe_ask()
        if choice == 'Set django address':
            address = questionary.text(
                "Enter django address:",
                validate=valid_uri
            ).unsafe_ask()
            set_django_address(address)
            print('Address set')
        elif choice == 'Sync current nodes from django':
            cli_config = sync_cli_config()
            print('Updated cli_config.json:')
            print(json.dumps(cli_config, indent=4))
        elif choice == 'Download all config files from django':
            download_all_node_config_files()
        elif choice == 'Done':
            break


def config_prompt():
    '''Prompt allows user to create config file or edit existing config'''
    choice = questionary.select(
        "\nWhat would you like to do?",
        choices=[
            "Generate new config",
            "Edit existing config",
            "Done"
        ]
    ).unsafe_ask()
    if choice == 'Generate new config':
        generator = GenerateConfigFile()
        generator.run_prompt()
        if generator.passed_validation:
            generator.write_to_disk()
    elif choice == 'Edit existing config':
        # Prompt to select node
        node = questionary.select(
            "\nSelect a node to edit",
            choices=list(cli_config['nodes'].keys())
        ).unsafe_ask()

        # Instantiate generator with path to node config
        generator = GenerateConfigFile(get_config_filepath(node))
        generator.run_prompt()
        if generator.passed_validation:
            generator.write_to_disk()


def provision_prompt():
    '''Prompt allows user to reprovision existing node or provision new node'''
    choice = questionary.select(
        "\nWhat would you like to do?",
        choices=[
            "Reupload config to existing node",
            "Upload config to new node",
            "Done"
        ]
    ).unsafe_ask()
    if choice == 'Reupload config to existing node':
        node = questionary.select(
            "\nSelect a node to reprovision",
            choices=list(cli_config['nodes'].keys())
        ).unsafe_ask()
        upload_node(node, cli_config['webrepl_password'])
    elif choice == 'Upload config to new node':
        # Prompt user for valid IPv4 address
        ip_address = questionary.text(
            "Enter IP address:",
            validate=valid_ip
        ).unsafe_ask()

        # Prompt user to select file from config_directory
        config = questionary.select(
            "\nWhat would you like to do?",
            choices=os.listdir(cli_config['config_directory'])
        ).unsafe_ask()

        upload_config_to_ip(
            config_path=os.path.join(cli_config['config_directory'], config),
            ip=ip_address,
            webrepl_password=cli_config['webrepl_password']
        )


def delete_prompt():
    '''Prompt allows user to delete existing nodes from cli_config.json. If a
    django server is configured the node is also removed from django database.
    '''
    targets = questionary.checkbox(
        "Select nodes to delete",
        choices=list(cli_config['nodes'].keys())
    ).unsafe_ask()

    # Print warning, show confirmation prompt
    print('The following nodes will be deleted:')
    for i in targets:
        print(f'  {i}')
    if cli_config['django_backend']:
        print('These nodes will also be deleted from the django database')
    choice = questionary.select(
        "\nThis cannot be undone, are you sure?",
        choices=[
            "Yes",
            "No"
        ]
    ).unsafe_ask()

    if choice == 'Yes':
        for i in targets:
            remove_node_from_cli_config(i)


def api_target_node_prompt():
    '''Prompts user to select a Node for api_prompt'''
    node = questionary.select(
        "Select target node",
        choices=list(cli_config['nodes'].keys())
    ).unsafe_ask()
    node_ip = cli_config['nodes'][node]
    return node, node_ip


def api_prompt():
    '''Prompt allows user to send API commands to existing nodes'''

    # Prompt to select existing node, get name and IP address
    node, node_ip = api_target_node_prompt()

    # Get API endpoint options, add Done (break loop)
    endpoint_options = list(example_usage.keys())
    endpoint_options.append('Done')

    while True:
        # Get status object, print current status (repeats after each command)
        status = parse_command(node_ip, ['status'])
        print(f'{node} status:')
        print(json.dumps(status, indent=4))

        # Prompt to select endpoint
        endpoint = questionary.select(
            "Select command",
            choices=endpoint_options
        ).unsafe_ask()

        # Create list with endpoint as first arg
        # Prompts below add additional args (if needed), result sent to node
        command_args = [endpoint]

        # Break loop when user selects Done
        if endpoint == 'Done':
            break

        # If selected endpoint requires device/sensor argument
        if endpoint in [
            'disable',
            'disable_in',
            'enable',
            'enable_in',
            'set_rule',
            'increment_rule',
            'reset_rule',
            'get_schedule_rules',
            'add_rule',
            'remove_rule',
            'get_attributes'
        ]:
            # Prompt to select from available devices and sensors
            target = questionary.select(
                "Select device or sensor",
                choices=list(status['devices'].keys()) + list(status['sensors'].keys())
            ).unsafe_ask()
            command_args.append(target)

            # If selected endpoint requires additional arg
            if endpoint in ['disable_in', 'enable_in']:
                arg = questionary.text(
                    "Enter delay (minutes):"
                ).unsafe_ask()
                command_args.append(arg)

            elif endpoint == 'set_rule':
                arg = questionary.text(
                    "Enter rule"
                ).unsafe_ask()
                command_args.append(arg)

            elif endpoint == 'increment_rule':
                arg = questionary.text(
                    "Enter amount to increment rule by (can be negative)"
                ).unsafe_ask()
                command_args.append(arg)

            elif endpoint == 'add_rule':
                # Prompt to enter timestamp or keyword
                timestamp = questionary.text(
                    "Enter timestamp (HH:MM) or keyword"
                ).unsafe_ask()
                command_args.append(timestamp)

                # Prompt to enter rule
                rule = questionary.text(
                    "Enter rule"
                ).unsafe_ask()
                command_args.append(rule)

            elif endpoint == 'remove_rule':
                # Get list of existing rules for target
                if target.startswith('device'):
                    rules = list(status['devices'][target]['schedule'].keys())
                else:
                    rules = list(status['sensors'][target]['schedule'].keys())

                # Prompt to select existing rule to remove
                rule = questionary.select(
                    'Select rule to remove',
                    choices=rules
                ).unsafe_ask()
                command_args.append(rule)

        # If selected endpoint requires device argument
        elif endpoint in ['turn_on', 'turn_off']:
            # Prompt to select from available devices
            target = questionary.select(
                "Select device or sensor",
                choices=list(status['devices'].keys())
            ).unsafe_ask()
            command_args.append(target)

        elif endpoint in ['trigger_sensor', 'condition_met']:
            # Prompt to select from available sensors
            target = questionary.select(
                "Select device or sensor",
                choices=list(status['sensors'].keys())
            ).unsafe_ask()
            command_args.append(target)

        elif endpoint == 'add_schedule_keyword':
            # Prompt user to enter keyword and timestamp
            keyword = questionary.text(
                'Enter new keyword name'
            ).unsafe_ask()
            command_args.append(keyword)

            timestamp = questionary.text(
                'Enter new keyword timestamp'
            ).unsafe_ask()
            command_args.append(timestamp)

        elif endpoint == 'remove_schedule_keyword':
            # Prompt user to select existing keyword to delete
            keyword = questionary.select(
                'Select keyword to delete',
                choices=list(status['metadata']['schedule_keywords'])
            ).unsafe_ask()
            command_args.append(keyword)

        elif endpoint == 'ir_create_macro':
            # Prompt user for new macro name
            arg = questionary.text(
                'Enter new macro name'
            ).unsafe_ask()
            command_args.append(arg)

        elif endpoint == 'set_gps_coords':
            # Prompt user for longitude and latitude
            latitude = questionary.text(
                'Enter latitude'
            ).unsafe_ask()
            command_args.append(latitude)

            longitude = questionary.text(
                'Enter longitude'
            ).unsafe_ask()
            command_args.append(longitude)

        # Send command, print response
        response = parse_command(node_ip, command_args)
        print(json.dumps(response, indent=4))
        questionary.press_any_key_to_continue().ask()


def main_prompt():
    '''Main menu prompt'''
    while True:
        choice = questionary.select(
            "\nWhat would you like to do?",
            choices=[
                "API client",
                "Configure node",
                "Provision node",
                "Delete node",
                "Settings",
                "Done"
            ]
        ).unsafe_ask()
        if choice == 'API client':
            api_prompt()
        elif choice == 'Configure node':
            config_prompt()
        elif choice == 'Provision node':
            provision_prompt()
        elif choice == 'Delete node':
            delete_prompt()
        elif choice == 'Settings':
            sync_prompt()
        elif choice == 'Done':
            break


if __name__ == '__main__':
    try:
        main_prompt()
    except KeyboardInterrupt as interrupt:
        raise SystemExit from interrupt
