'''Loads cli_config.json from disk and exposes methods to read and modify'''

import os
import json
import requests
from helper_functions import get_cli_config_name, get_config_filename

# Get path to cli_config.json (same directory as class)
cli = os.path.dirname(os.path.realpath(__file__))
repo = os.path.split(cli)[0]
cli_config_path = os.path.join(cli, 'cli_config.json')


class CliConfigManager:
    '''Loads cli_config.json from disk and exposes methods to read and modify'''

    def __init__(self):
        self.config = self.read_cli_config_from_disk()

    def read_cli_config_from_disk(self):
        '''Reads cli_config.json from disk and returns parsed contents'''
        try:
            with open(cli_config_path, 'r', encoding='utf-8') as file:
                return json.load(file)
        except FileNotFoundError:
            print("Warning: Unable to find cli_config.json, using template")
            return {
                'nodes': {},
                'schedule_keywords': {},
                'webrepl_password': 'password',
                'config_directory': os.path.join(repo, 'config_files')
            }

    def write_cli_config_to_disk(self):
        '''Overwrites cli_config.json with current contents of self.config'''
        with open(cli_config_path, 'w', encoding='utf-8') as file:
            json.dump(self.config, file, indent=4)

    def sync_nodes_from_django(self):
        '''Updates config contents with nodes from django database.
        Must set django server address in cli_config.json.
        '''
        if not self.config['django_backend']:
            raise RuntimeError('No django backend configured')

        # Request dict of existing nodes from backend
        response = requests.get(
            f'{self.config["django_backend"]}/get_nodes',
            timeout=5
        )
        if response.status_code == 200:
            # Merge response dict into cli_config with union operator
            self.config['nodes'] |= response.json()['message']
            self.write_cli_config_to_disk()
        else:
            print('Failed to sync nodes')

    def sync_schedule_keywords_from_django(self):
        '''Updates config contents with schedule keywords from django database.
        Must set django server address in cli_config.json.
        '''
        if not self.config['django_backend']:
            raise RuntimeError('No django backend configured')

        # Request dict of existing nodes from backend
        response = requests.get(
            f'{self.config["django_backend"]}/get_schedule_keywords',
            timeout=5
        )
        if response.status_code == 200:
            # Merge response dict into cli_config with union operator
            self.config['schedule_keywords'] |= response.json()['message']
            self.write_cli_config_to_disk()
        else:
            print('Failed to sync keywords')

    def get_existing_node_names(self):
        '''Returns list of node names in cli_config.json nodes section'''
        return list(self.config['nodes'].keys())

    def add_node(self, name, ip):
        '''Takes name and IP of new node, adds to cli_config.json'''

        # Ensure name has no spaces (cli_config.json syntax)
        name = get_cli_config_name(name)

        # Add to nodes section with cli-safe name as key, IP as value
        self.config['nodes'][name] = ip
        self.write_cli_config_to_disk()

        # If django backend configured add new node to database
        if 'django_backend' in self.config:
            print('Uploading node to django database...')
            requests.post(
                f'{self.config["django_backend"]}/add_node',
                json.dumps({
                    'ip': ip,
                    'config': self.load_node_config_file(name)
                }),
                timeout=5
            )
            print('Done.')

    def remove_node(self, name):
        '''Takes node config name, deletes from cli_config.json'''

        # Ensure name has no spaces (cli_config.json syntax)
        name = get_cli_config_name(name)

        try:
            del self.config['nodes'][name]
            self.write_cli_config_to_disk()

            # If django backend configured delete node from database
            if 'django_backend' in self.config:
                print(f'Deleting {name} from django database...')

                try:
                    # Load config, get friendly name
                    config = self.load_node_config_file(name)
                    friendly_name = config['metadata']['id']

                    # Post friendly name to backend
                    requests.post(
                        f'{self.config["django_backend"]}/delete_node',
                        json.dumps(friendly_name),
                        timeout=5
                    )
                    print('Done.')
                except FileNotFoundError:
                    print('Failed to delete from django database')
        except KeyError:
            pass

    def get_config_filepath(self, friendly_name):
        '''Takes friendly_name, returns path to config file. Does not check if
        file exists, can be used to get path for new file or to find existing.
        '''
        filename = get_config_filename(friendly_name)
        return os.path.join(self.config['config_directory'], filename)

    def load_node_config_file(self, friendly_name):
        '''Takes friendly_name of existing node, reads matching config file in
        config_directory (set in cli_config.json), returns contents.
        '''
        config_filepath = self.get_config_filepath(friendly_name)
        if not os.path.exists(config_filepath):
            raise FileNotFoundError
        with open(config_filepath, 'r', encoding='utf-8') as file:
            config = json.load(file)
        return config

    def save_node_config_file(self, config):
        '''Takes config file dict, generates filename from config.metadata.id,
        creates or overwrites file in config_directory (set in cli_config.json).
        '''
        try:
            config_filepath = self.get_config_filepath(config['metadata']['id'])
            with open(config_filepath, 'w', encoding='utf-8') as file:
                json.dump(config, file)
            return config_filepath
        except KeyError as exception:
            raise ValueError('config file has no name') from exception

    def set_django_address(self, address):
        '''Takes django backend URI, updates config and writes to disk'''
        self.config['django_backend'] = address
        self.write_cli_config_to_disk()

    def set_config_directory(self, path):
        '''Takes path to config_directory, updates config and writes to disk'''
        self.config['config_directory'] = path
        self.write_cli_config_to_disk()

    def set_webrepl_password(self, password):
        '''Takes webrepl password, updates config and writes to disk'''
        self.config['webrepl_password'] = password
        self.write_cli_config_to_disk()
