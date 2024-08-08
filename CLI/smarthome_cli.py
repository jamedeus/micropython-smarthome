#!/usr/bin/env python3

'''Main CLI script'''

import os
import json
import pydoc
import requests
import questionary
from Webrepl import Webrepl
from helper_functions import valid_ip, valid_uri, get_config_filename
from config_generator import GenerateConfigFile
from config_prompt_validators import LengthRange
from provision import upload_node, upload_config_to_ip
from api_client import api_prompt
from cli_config_manager import CliConfigManager


# Read cli_config.json from disk
cli_config = CliConfigManager()


def download_all_node_config_files():
    '''Iterates nodes in cli_config.json, downloads each config file from
    backend and writes to config_dir (set in cli_config.json).
    '''
    for node, ip in cli_config.config['nodes'].items():
        config = download_node_config_file(ip)
        if config:
            # Create JSON config file in config_directory
            cli_config.save_node_config_file(config)
            print(f'Downloaded {node} config file')

        else:
            print(f'Failed to download {node} config file')


def download_node_config_file(ip):
    '''Takes node IP, requests config file from backend and returns'''
    response = requests.get(
        f'{cli_config.config["django_backend"]}/get_node_config/{ip}',
        timeout=5
    )
    if response.status_code == 200:
        return response.json()['message']
    return False


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
                "Change config config directory",
                "Change webrepl password",
                "Done"
            ]
        ).unsafe_ask()
        if choice == 'Set django address':
            address = questionary.text(
                "Enter django address:",
                validate=valid_uri
            ).unsafe_ask()
            cli_config.set_django_address(address)
            print('Address set')
        elif choice == 'Sync current nodes from django':
            cli_config.sync_nodes_from_django()
            cli_config.sync_schedule_keywords_from_django()
            print('Updated cli_config.json:')
            print(json.dumps(cli_config.config, indent=4))
        elif choice == 'Download all config files from django':
            download_all_node_config_files()
        elif choice == 'Change config config directory':
            directory = questionary.text(
                'Enter absolute path to config directory'
            ).unsafe_ask()
            cli_config.set_config_directory(directory)
            print('Config directory set')
        elif choice == 'Change webrepl password':
            password = questionary.text(
                'Enter new password',
                validate=LengthRange(4, 9)
            ).unsafe_ask()
            cli_config.set_webrepl_password(password)
            print('Password set')
        elif choice == 'Done':
            break


def delete_prompt():
    '''Prompt allows user to delete existing nodes from cli_config.json. If a
    django server is configured the node is also removed from django database.
    '''
    targets = questionary.checkbox(
        "Select nodes to delete",
        choices=cli_config.get_existing_node_names()
    ).unsafe_ask()

    # Print warning, show confirmation prompt
    print('The following nodes will be deleted:')
    for i in targets:
        print(f'  {i}')
    if cli_config.config['django_backend']:
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
            cli_config.remove_node(i)


def view_log_prompt():
    '''Prompt allows user to download and view log from an existing node'''
    node = questionary.select(
        "\nSelect a node to view log",
        choices=list(cli_config.config['nodes'].keys())
    ).unsafe_ask()

    # Open connection, download log
    ip = cli_config.config['nodes'][node]
    connection = Webrepl(ip, cli_config.config['webrepl_password'])
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


def upload_config_from_disk(config=None):
    '''Prompt allows user to select file in config_directory, upload to IP.
    Only prompts for IP if path to config file given as argument.
    '''

    # Prompt user for valid IPv4 address
    ip_address = questionary.text(
        "Enter IP address:",
        validate=valid_ip
    ).unsafe_ask()

    # Prompt user to select file from config_directory
    if not config:
        config = questionary.select(
            "\nWhat would you like to do?",
            choices=os.listdir(cli_config.config['config_directory'])
        ).unsafe_ask()
    print(config)

    # Upload config to target IP (also adds to cli_config.json)
    upload_config_to_ip(
        config_path=os.path.join(cli_config.config['config_directory'], config),
        ip=ip_address,
        webrepl_password=cli_config.config['webrepl_password']
    )

    # Read updated cli_config.json from disk
    print('updating from disk')
    cli_config.read_cli_config_from_disk()
    print(cli_config.config['nodes'])


def create_new_node_prompt():
    '''Prompt allows user to create config file, upload to new node'''

    # Show config generator prompt
    generator = GenerateConfigFile()
    generator.run_prompt()
    if generator.passed_validation:
        generator.write_to_disk()

    if questionary.confirm('Upload config to ESP32?').ask():
        filename = get_config_filename(generator.config['metadata']['id'])
        upload_config_from_disk(filename)


def edit_node_config_prompt():
    '''Prompt allows user to select existing node, edit config, reupload'''

    # Prompt to select node
    node = questionary.select(
        "\nSelect a node to edit",
        choices=list(cli_config.config['nodes'].keys())
    ).unsafe_ask()

    # Instantiate generator with path to node config
    generator = GenerateConfigFile(cli_config.get_config_filepath(node))
    generator.run_prompt()
    if generator.passed_validation:
        generator.write_to_disk()

    # Upload modified config to node
    if questionary.confirm('Reupload now?'):
        print(f'Reuploading {node}.json... ')
        upload_node(node, cli_config.config['webrepl_password'])


def manage_nodes_prompt():
    '''Prompt allows user to create config files, provision nodes, etc'''
    while True:
        choice = questionary.select(
            "\nWhat would you like to do?",
            choices=[
                "Create new node",
                "Edit existing node config",
                "Reupload config to node",
                "Upload config file from disk",
                "Delete existing node",
                "View node log",
                "Done"
            ]
        ).unsafe_ask()

        if choice == 'Create new node':
            create_new_node_prompt()

        elif choice == 'Edit existing node config':
            edit_node_config_prompt()

        elif choice == 'Reupload config to node':
            node = questionary.select(
                "\nSelect a node to reprovision",
                choices=list(cli_config.config['nodes'].keys())
            ).unsafe_ask()
            upload_node(node, cli_config.config['webrepl_password'])

        elif choice == 'Upload config file from disk':
            upload_config_from_disk()

        elif choice == 'Delete existing node':
            delete_prompt()

        elif choice == 'View node log':
            view_log_prompt()

        elif choice == 'Done':
            break


def main_prompt():
    '''Main menu prompt'''
    while True:
        choice = questionary.select(
            "\nWhat would you like to do?",
            choices=[
                "API client",
                "Manage nodes",
                "Settings",
                "Done"
            ]
        ).unsafe_ask()
        if choice == 'API client':
            api_prompt()
        elif choice == 'Manage nodes':
            manage_nodes_prompt()
        elif choice == 'Settings':
            sync_prompt()
        elif choice == 'Done':
            break


if __name__ == '__main__':
    try:
        main_prompt()
    except KeyboardInterrupt as interrupt:
        raise SystemExit from interrupt
