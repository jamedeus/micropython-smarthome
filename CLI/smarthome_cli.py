#!/usr/bin/env python3

'''Main CLI script'''

import json
import requests
from helper_functions import (
    get_cli_config,
    write_cli_config,
    get_config_filepath
)


cli_config = get_cli_config()


def sync_cli_config():
    '''Updates cli_config.json with values from django database'''

    # Request dict of existing nodes from backend
    response = requests.get(
        f'{cli_config["django_backend"]}/get_nodes',
        timeout=5
    )
    if response.status_code == 200:
        nodes = response.json()['message']
        for node, params in nodes.items():
            if node in cli_config['nodes']:
                cli_config['nodes'][node]['ip'] = params['ip']
            else:
                cli_config['nodes'][node] = params
    else:
        print('Failed to sync nodes')

    # Request dict of existing schedule keywords from backend
    response = requests.get(
        f'{cli_config["django_backend"]}/get_schedule_keywords',
        timeout=5
    )
    if response.status_code == 200:
        keywords = response.json()['message']
        cli_config['schedule_keywords'] = cli_config['schedule_keywords'] | keywords
    else:
        print('Failed to sync keywords')

    write_cli_config(cli_config)


def download_all_node_config_files():
    '''Iterates nodes in cli_config.json, downloads each config file from
    backend and writes to config_dir (set in cli_config.json).
    '''
    for node, params in cli_config['nodes'].items():
        config = download_node_config_file(params['ip'])
        if config:
            # Create JSON config file in config_directory
            config_path = get_config_filepath(node)
            with open(config_path, 'w', encoding='utf-8') as file:
                json.dump(config, file)

            # Add config file path to cli_config.json
            cli_config['nodes'][node]['config'] = config_path
            write_cli_config(cli_config)

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
