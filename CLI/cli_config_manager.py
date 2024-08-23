'''Loads cli_config.json from disk and exposes methods to read and modify'''

import os
import json
import urllib3
import requests
import questionary
from provision_tools import get_modules, provision
from helper_functions import get_cli_config_name, get_config_filename
from api_helper_functions import (
    bulk_add_schedule_keyword,
    bulk_edit_schedule_keyword,
    bulk_remove_schedule_keyword,
    bulk_save_schedule_keyword
)

# Get path repository root directory
cli = os.path.dirname(os.path.realpath(__file__))
repo = os.path.split(cli)[0]


def get_system_config_directory():
    '''Returns platform-dependent path to user config directory.
    Unix: Returns ~/.config
    Windows: Returns AppData path
    '''
    return os.environ.get('APPDATA') or os.environ.get('XDG_CONFIG_HOME') or os.path.join(
        os.environ.get('HOME'),
        '.config'
    )


def get_app_config_directory():
    '''Returns platform-dependent path to smarthome_cli config directory.'''

    # Get path to smarthome_cli subdir inside system config directory
    app_config_dir = os.path.join(
        get_system_config_directory(),
        'smarthome_cli'
    )

    # Create smarthome_cli subdir if it doesn't exist
    if not os.path.exists(app_config_dir):
        os.mkdir(app_config_dir)

    return app_config_dir


def get_cli_config_path():
    '''Returns path to cli_config.json inside smarthome_cli config directory.
    Unix: Returns ~/.config/smarthome_cli/cli_config.json
    Windows: Returns path to smarthome_cli/cli_config.json inside AppData
    '''
    return os.path.join(get_app_config_directory(), 'cli_config.json')


def get_default_cli_config():
    '''Returns default cli_config.json template, called when cli_config.json
    does not exist on disk. Creates directory for ESP32 config files if the
    default directory does not exist.
    '''

    # Get default config_directory, create if doesn't exist
    # Unix: ~/.config/smarthome_cli/config_files/
    # Windows: AppData/smarthome_cli/config_files/
    config_directory = os.path.join(
        get_app_config_directory(),
        'config_files'
    )
    if not os.path.exists(config_directory):
        os.mkdir(config_directory)

    return {
        'nodes': {},
        'schedule_keywords': {},
        'webrepl_password': 'password',
        'config_directory': config_directory
    }


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
            with open(get_cli_config_path(), 'r', encoding='utf-8') as file:
                return json.load(file)
        except FileNotFoundError:
            return get_default_cli_config()

    def write_cli_config_to_disk(self):
        '''Overwrites cli_config.json with current contents of self.config'''
        with open(get_cli_config_path(), 'w', encoding='utf-8') as file:
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

            # Disable SSL certificate verification if ignore_ssl_errors set
            if self.config.get('ignore_ssl_errors'):
                self._client.verify = False
                urllib3.disable_warnings(
                    urllib3.exceptions.InsecureRequestWarning
                )

        # Request dict of existing nodes from backend
        try:
            response = self._client.get(
                f'{self.config["django_backend"]}/get_cli_config',
                timeout=5
            )
        except requests.exceptions.ConnectionError:
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
            try:
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
            except requests.exceptions.ConnectionError:
                print('Failed to add to django database (connection error)')

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
                except requests.exceptions.ConnectionError:
                    print('Failed to delete from django database (connection error)')
        except KeyError:
            pass

    def change_node_ip(self, name, ip):
        '''Takes name of existing node and new IP address, reuploads config to
        new IP and updates cli_config.json if successful. If Django backend is
        configured sends POST request to update IP in django database.
        '''

        # Load node config file from disk
        config = self.load_node_config_file(name)

        # Upload config to new IP
        result = provision(
            ip=ip,
            password=self.config['webrepl_password'],
            config=config,
            modules=get_modules(config, repo)
        )

        # Update IP in cli_config.json if upload successful
        if result['status'] == 200:
            self.config['nodes'][name] = ip
            self.write_cli_config_to_disk()

            # If django backend configured change IP in django database
            if 'django_backend' in self.config:
                print('Changing IP in django database...')
                try:
                    response = self._client.post(
                        f'{self.config["django_backend"]}/change_node_ip',
                        json={
                            'friendly_name': config['metadata']['id'],
                            'new_ip': ip,
                            'reupload': False
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
                except requests.exceptions.ConnectionError:
                    print('Failed to update django database (connection error)')

        # Print error from provision if upload failed
        else:
            print(result['message'])

    def add_schedule_keyword(self, keyword, timestamp):
        '''Takes new keyword name and timestamp, adds to cli_config.json and
        makes API calls to add keyword to all existing nodes.
        '''

        # Add to cli_config.json, write to disk
        self.config['schedule_keywords'][keyword] = timestamp
        self.write_cli_config_to_disk()

        # Add keyword to all existing nodes in parallel
        node_ips = list(self.config['nodes'].values())
        bulk_add_schedule_keyword(node_ips, keyword, timestamp)
        bulk_save_schedule_keyword(node_ips)

        # If django configured make API call to add keyword to database
        if 'django_backend' in self.config:
            try:
                self._client.post(
                    f'{self.config["django_backend"]}/add_schedule_keyword',
                    json={
                        'keyword': keyword,
                        'timestamp': timestamp,
                        'sync_nodes': False
                    },
                    headers={
                        'X-CSRFToken': self._csrf_token
                    },
                    timeout=5
                )
            except requests.exceptions.ConnectionError:
                print('Failed to add to django database (connection error)')

    def edit_schedule_keyword(self, keyword_old, keyword_new, timestamp):
        '''Takes name of existing keyword, new name (can be same), and new
        timestamp (can be same). Updates cli_config.json and makes API calls
        to update keyword on all existing nodes.
        '''

        # If keyword name was changed delete old keyword
        if keyword_old != keyword_new:
            del self.config['schedule_keywords'][keyword_old]

        # Add new keyword to cli_config.json, write to disk
        self.config['schedule_keywords'][keyword_new] = timestamp
        self.write_cli_config_to_disk()

        # Update keyword on all existing nodes in parallel
        node_ips = list(self.config['nodes'].values())
        bulk_edit_schedule_keyword(node_ips, keyword_old, keyword_new, timestamp)
        bulk_save_schedule_keyword(node_ips)

        # If django configured make API call to edit keyword in database
        if 'django_backend' in self.config:
            try:
                self._client.post(
                    f'{self.config["django_backend"]}/edit_schedule_keyword',
                    json={
                        'keyword_old': keyword_old,
                        'keyword_new': keyword_new,
                        'timestamp_new': timestamp,
                        'sync_nodes': False
                    },
                    headers={
                        'X-CSRFToken': self._csrf_token
                    },
                    timeout=5
                )
            except requests.exceptions.ConnectionError:
                print('Failed to update django database (connection error)')

    def remove_schedule_keyword(self, keyword):
        '''Takes name of existing keyword, removes from cli_config.json and
        makes API calls to remove from all existing nodes.
        '''

        # Remove from cli_config.json, write to disk
        del self.config['schedule_keywords'][keyword]
        self.write_cli_config_to_disk()

        # Update keyword on all existing nodes in parallel
        node_ips = list(self.config['nodes'].values())
        bulk_remove_schedule_keyword(node_ips, keyword)
        bulk_save_schedule_keyword(node_ips)

        # If django configured make API call to remove keyword from database
        if 'django_backend' in self.config:
            try:
                self._client.post(
                    f'{self.config["django_backend"]}/delete_schedule_keyword',
                    json={
                        'keyword': keyword,
                        'sync_nodes': False
                    },
                    headers={
                        'X-CSRFToken': self._csrf_token
                    },
                    timeout=5
                )
            except requests.exceptions.ConnectionError:
                print('Failed to remove from django database (connection error)')

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
        if 'django_backend' in self.config:
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

        try:
            response = self._client.get(
                f'{self.config["django_backend"]}/get_node_config/{ip}',
                timeout=5
            )
            if response.status_code == 200:
                return response.json()['message']
        except requests.exceptions.ConnectionError:
            print('Failed to download config from django database (connection error)')
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

        # Close open connections (if any), clear cookies (avoid duplicate csrf)
        if self._client:
            self._client.close()
            self._client.cookies.clear()

    def set_config_directory(self, path):
        '''Takes path to config_directory, updates config and writes to disk'''
        self.config['config_directory'] = path
        self.write_cli_config_to_disk()

    def set_webrepl_password(self, password):
        '''Takes webrepl password, updates config and writes to disk'''
        self.config['webrepl_password'] = password
        self.write_cli_config_to_disk()
