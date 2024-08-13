'''Loads cli_config.json from disk and exposes methods to read and modify'''

import os
import json
import requests
import questionary
from helper_functions import get_cli_config_name, get_config_filename

# Get path to cli_config.json (same directory as class)
cli = os.path.dirname(os.path.realpath(__file__))
repo = os.path.split(cli)[0]
cli_config_path = os.path.join(cli, 'cli_config.json')


class CliConfigManager:
    '''Loads cli_config.json from disk and exposes methods to read and modify.

    Singleton class, all modules that instantiate receive the same instance to
    ensure config contents remain in sync (example: if user runs smarthome_cli
    and creates a new node the CliConfigManager instance in provision.py will
    call add_node, the smarthome_cli instance. Without singleton the new node
    would not appear in smarthome_cli menu until the script was restarted).
    '''

    _instance = None
    _initialized = False

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(CliConfigManager, cls).__new__(cls, *args, **kwargs)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        # Load cli_config.json from disk
        self.config = self.read_cli_config_from_disk()

        # Used for POST requests if django_backend configured
        self._client = None
        self._csrf_token = None

        # If django server configured sync nodes and keywords
        if 'django_backend' in self.config:
            self.sync_from_django()

        self._initialized = True

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

    def sync_from_django(self):
        '''Updates config contents with nodes and schedule keywords from django
        database (must set django server address in cli_config.json).
        '''
        if 'django_backend' not in self.config:
            raise RuntimeError('No django backend configured')

        # Open session on first run
        if not self._client:
            self._client = requests.session()

        # Request dict of existing nodes from backend
        try:
            response = self._client.get(
                f'{self.config["django_backend"]}/get_cli_config',
                timeout=5
            )
        except OSError:
            print('Failed to sync from django (connection refused)')
            return
        if response.status_code == 200:
            # Merge response dict into cli_config with union operator
            update = response.json()['message']
            self.config['nodes'] |= update['nodes']
            self.config['schedule_keywords'] |= update['schedule_keywords']

            # Write updated cli_config.json to disk
            self.write_cli_config_to_disk()

            # Save CSRF token (used for POST requests to django)
            self._csrf_token = self._client.cookies['csrftoken']
        else:
            print('Failed to sync from django')

    def get_existing_node_names(self):
        '''Returns list of node names in cli_config.json nodes section'''
        return list(self.config['nodes'].keys())

    def add_node(self, config, ip):
        '''Takes config dict and IP of new node, adds to cli_config.json.
        If Django backend configured sends POST request to add to database.
        '''

        # Ensure name has no spaces (cli_config.json syntax)
        name = get_cli_config_name(config['metadata']['id'])

        # Add to nodes section with cli-safe name as key, IP as value
        self.config['nodes'][name] = ip
        self.write_cli_config_to_disk()

        # If django backend configured add new node to database
        if 'django_backend' in self.config:
            print('Uploading node to django database...')
            response = self._client.post(
                f'{self.config["django_backend"]}/add_node',
                json={
                    'ip': ip,
                    'config': config
                },
                headers={
                    'X-CSRFToken': self._csrf_token
                },
                timeout=5
            )
            if response.status_code == 200:
                print('Done.')
            else:
                print(response.text)

        # Write config to config_directory if file doesn't exist (can happen
        # if provision called with path to config file in other directory)
        if not os.path.exists(self.get_config_filepath(name)):
            self.save_node_config_file(config)

    def remove_node(self, name):
        '''Takes node config name, deletes from cli_config.json'''

        # Ensure name has no spaces (cli_config.json syntax)
        name = get_cli_config_name(name)

        try:
            # Get IP before deleting (used in django request payload)
            ip = self.config['nodes'][name]

            # Delete from cli_config.json, write to disk
            del self.config['nodes'][name]
            self.write_cli_config_to_disk()

            # If django backend configured delete node from database
            if 'django_backend' in self.config:
                print(f'Deleting {name} from django database...')

                try:
                    # Post friendly name to backend
                    response = self._client.post(
                        f'{self.config["django_backend"]}/delete_node',
                        json={'ip': ip},
                        headers={
                            'X-CSRFToken': self._csrf_token
                        },
                        timeout=5
                    )
                    if response.status_code == 200:
                        print('Done.')
                    else:
                        print(response.text)
                except (OSError):
                    print('Failed to delete from django database (connection error)')
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
        if os.path.exists(config_filepath):
            with open(config_filepath, 'r', encoding='utf-8') as file:
                config = json.load(file)
            return config

        # If missing from disk + django configured prompt user to download file
        elif 'django_backend' in self.config:
            if questionary.confirm(
                f'{friendly_name} config missing from disk, download from django?'
            ).ask():
                # Download from django backend, write to disk, return
                ip = self.config['nodes'][get_cli_config_name(friendly_name)]
                config = self.download_node_config_file_from_django(ip)
                self.save_node_config_file(config)
                return config

        # Raise exception if unable to load config
        raise FileNotFoundError


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

    def download_node_config_file_from_django(self, ip):
        '''Takes IP of existing node in cli_config.json, requests config file
        from django backend, returns config dict.
        '''
        if 'django_backend' not in self.config:
            raise RuntimeError('No django backend configured')

        response = self._client.get(
            f'{self.config["django_backend"]}/get_node_config/{ip}',
            timeout=5
        )
        if response.status_code == 200:
            return response.json()['message']
        return False

    def download_all_node_config_files_from_django(self):
        '''Iterates existing nodes in cli_config.json, downloads each config
        file from django backend and writes to config_directory.
        '''
        if 'django_backend' not in self.config:
            raise RuntimeError('No django backend configured')

        for node, ip in self.config['nodes'].items():
            config = self.download_node_config_file_from_django(ip)
            if config:
                # Create JSON config file in config_directory
                self.save_node_config_file(config)
                print(f'Downloaded {node} config file')

            else:
                print(f'Failed to download {node} config file')

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
