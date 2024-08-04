#!/usr/bin/env python3

'''Main CLI script'''

import json
import requests
import questionary
from helper_functions import (
    valid_uri,
    get_cli_config,
    write_cli_config,
    save_node_config_file,
    get_config_filepath
)
from config_generator import GenerateConfigFile


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


def main_prompt():
    '''Main menu prompt'''
    while True:
        choice = questionary.select(
            "\nWhat would you like to do?",
            choices=[
                "Generate config file",
                "Edit config file",
                "Django sync settings",
                "Done"
            ]
        ).unsafe_ask()
        if choice == 'Generate config file':
            generator = GenerateConfigFile()
            generator.run_prompt()
            if generator.passed_validation:
                generator.write_to_disk()
        elif choice == 'Edit config file':
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
        elif choice == 'Django sync settings':
            sync_prompt()
        elif choice == 'Done':
            break


if __name__ == '__main__':
    main_prompt()
