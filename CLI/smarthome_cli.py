#!/usr/bin/env python3

'''Main CLI script'''

import os
import json
import pydoc
import requests
import questionary
from Webrepl import Webrepl
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
from api_client import api_prompt


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


def view_log_prompt():
    '''Prompt allows user to download and view log from an existing node'''
    node = questionary.select(
        "\nSelect a node to view log",
        choices=list(cli_config['nodes'].keys())
    ).unsafe_ask()

    # Open connection, download log
    ip = cli_config['nodes'][node]
    connection = Webrepl(ip, cli_config['webrepl_password'])
    print('Downloading log, this may take a few minutes...')
    log = connection.get_file_mem('app.log')

    # Display log in pager
    pydoc.pager(log.decode())

    # Save log prompt
    if questionary.confirm('Save log?').ask():
        filename = questionary.text(
            'Enter filename',
            default=f'{node}.log'
        ).ask()
        with open(filename, 'w', encoding='utf-8') as file:
            file.write(log.decode())
        print(f'Log saved as {filename}')


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
                "View node log",
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
        elif choice == 'View node log':
            view_log_prompt()
        elif choice == 'Settings':
            sync_prompt()
        elif choice == 'Done':
            break


if __name__ == '__main__':
    try:
        main_prompt()
    except KeyboardInterrupt as interrupt:
        raise SystemExit from interrupt
