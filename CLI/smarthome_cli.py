#!/usr/bin/env python3

'''Main CLI script'''

import os
import json
import pydoc
import questionary
from Webrepl import Webrepl
from helper_functions import valid_ip, valid_uri, valid_timestamp, get_config_filename
from config_generator import GenerateConfigFile
from config_prompt_validators import LengthRange
from provision import upload_node, upload_config_to_ip
from api_client import api_prompt
from cli_config_manager import CliConfigManager


# Read cli_config.json from disk
cli_config = CliConfigManager()


def settings_prompt():
    '''Prompt allows user to configure django server to sync from, update
    cli_config.json from django database, or download config files from django.
    '''
    choice = None
    while choice != 'Done':
        # Only show django sync options if address configured
        if 'django_backend' in cli_config.config:
            choices = [
                "Set django address",
                "Sync nodes and keywords from django",
                "Download all config files from django",
                "Change config directory",
                "Change webrepl password",
                "Done"
            ]
        else:
            choices = [
                "Set django address",
                "Change config directory",
                "Change webrepl password",
                "Done"
            ]

        choice = questionary.select(
            "\nWhat would you like to do?",
            choices=choices
        ).unsafe_ask()
        if choice == 'Set django address':
            address = questionary.text(
                "Enter django address:",
                validate=valid_uri
            ).unsafe_ask()
            cli_config.set_django_address(address)
            print('Address set')
        elif choice == 'Sync nodes and keywords from django':
            cli_config.sync_from_django()
            print('Updated cli_config.json:')
            print(json.dumps(cli_config.config, indent=4))
        elif choice == 'Download all config files from django':
            cli_config.download_all_node_config_files_from_django()
        elif choice == 'Change config directory':
            directory = questionary.path(
                'Enter absolute path to config directory',
                default=cli_config.config['config_directory'],
                validate=os.path.exists
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


def manage_nodes_prompt():
    '''Prompt allows user to create config files, provision nodes, etc'''
    choice = None
    while choice != 'Done':
        choice = questionary.select(
            "\nWhat would you like to do?",
            choices=[
                "Create new node",
                "Edit existing node config",
                "Reupload config to node",
                "Upload config file from disk",
                "Change existing node IP",
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

        elif choice == 'Change existing node IP':
            change_node_ip_prompt()

        elif choice == 'Delete existing node':
            delete_node_prompt()

        elif choice == 'View node log':
            view_log_prompt()


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
    if questionary.confirm('Reupload now?').ask():
        print(f'Reuploading {node}.json... ')
        upload_node(node, cli_config.config['webrepl_password'])


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
            "\nSelect config file",
            choices=os.listdir(cli_config.config['config_directory'])
        ).unsafe_ask()
    print(config)

    # Upload config to target IP (also adds to cli_config.json)
    upload_config_to_ip(
        config_path=os.path.join(cli_config.config['config_directory'], config),
        ip=ip_address,
        webrepl_password=cli_config.config['webrepl_password']
    )


def change_node_ip_prompt():
    '''Prompt allows user to change the IP address of an existing node (uploads
    config to new IP and changes in cli_config.json). If a django server is
    configured the IP is also changed in django database.
    '''

    # Prompt user to select existing node
    node = questionary.select(
        "\nSelect a node to change IP",
        choices=list(cli_config.config['nodes'].keys())
    ).unsafe_ask()

    # Prompt user for valid IPv4 address
    ip_address = questionary.text(
        "Enter new IP address:",
        validate=valid_ip
    ).unsafe_ask()

    # Reupload config to new IP and update cli_config.json if successful
    cli_config.change_node_ip(node, ip_address)


def delete_node_prompt():
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
    if 'django_backend' in cli_config.config:
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
        ).unsafe_ask()
        with open(filename, 'w', encoding='utf-8') as file:
            file.write(log.decode())
        print(f'Log saved as {filename}')


def manage_keywords_prompt():
    '''Prompt allows user to create, edit, and delete schedule keywords'''
    choice = None
    while choice != 'Done':
        choice = questionary.select(
            "\nWhat would you like to do?",
            choices=[
                "Add new schedule keyword",
                "Edit schedule keyword",
                "Delete schedule keyword",
                "Done"
            ]
        ).unsafe_ask()

        if choice == 'Add new schedule keyword':
            add_schedule_keyword_prompt()

        elif choice == 'Edit schedule keyword':
            edit_schedule_keyword_prompt()

        elif choice == 'Delete schedule keyword':
            remove_schedule_keyword_prompt()


def add_schedule_keyword_prompt():
    '''Prompts user to enter name and timestamp of new schedule keyword.
    Adds keyword to cli_config.json and makes API calls to all existing nodes.
    '''

    # Prompt user to enter keyword name and timestamp
    keyword = questionary.text("Enter new keyword name").unsafe_ask()
    timestamp = questionary.text(
        'Enter new keyword timestamp',
        validate=valid_timestamp
    ).unsafe_ask()

    print('Adding keyword to all existing nodes...')
    cli_config.add_schedule_keyword(keyword, timestamp)
    print('Done')


def edit_schedule_keyword_prompt():
    '''Prompts user to select an existing schedule keyword and change its name,
    timestamp, or both. Updates keyword in cli_config.json and makes API calls
    to all existing nodes.
    '''

    # Prompt to select keyword
    keyword_old = questionary.select(
        "\nSelect keyword to edit",
        choices=list(cli_config.config['schedule_keywords'].keys())
    ).unsafe_ask()

    # Prompt user to change name (optional)
    if questionary.confirm('Change name?').unsafe_ask():
        keyword_new = questionary.text("Enter new name").unsafe_ask()
    else:
        keyword_new = keyword_old

    # Prompt user to change timestamp (optional)
    if questionary.confirm('Change timestamp?').unsafe_ask():
        timestamp = questionary.text(
            'Enter new keyword timestamp',
            validate=valid_timestamp
        ).unsafe_ask()
    else:
        timestamp = cli_config.config['schedule_keywords'][keyword_old]

    print('Updating keyword on all existing nodes...')
    cli_config.edit_schedule_keyword(keyword_old, keyword_new, timestamp)
    print('Done')


def remove_schedule_keyword_prompt():
    '''Prompts user to select an existing schedule keyword to delete.
    Removes from cli_config.json and makes API calls to all existing nodes.
    '''

    # Prompt to select keyword
    keyword = questionary.select(
        "\nSelect keyword to delete",
        choices=list(cli_config.config['schedule_keywords'].keys())
    ).unsafe_ask()

    print('Removing keyword from all existing nodes...')
    cli_config.remove_schedule_keyword(keyword)
    print('Done')


def main_prompt():
    '''Main menu prompt'''
    choice = None
    while choice != 'Done':
        choice = questionary.select(
            "\nWhat would you like to do?",
            choices=[
                "API client",
                "Manage nodes",
                "Manage schedule keywords",
                "Settings",
                "Done"
            ]
        ).unsafe_ask()
        if choice == 'API client':
            api_prompt()
        elif choice == 'Manage nodes':
            manage_nodes_prompt()
        elif choice == 'Manage schedule keywords':
            manage_keywords_prompt()
        elif choice == 'Settings':
            settings_prompt()


if __name__ == '__main__':  # pragma: no cover
    try:
        main_prompt()
    except KeyboardInterrupt as interrupt:
        raise SystemExit from interrupt
