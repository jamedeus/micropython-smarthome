'''Utility functions used by both CLI tools and django backend'''

import re
import os
import json
import requests


# Get full path to repository root directory
util = os.path.dirname(os.path.realpath(__file__))
repo = os.path.split(util)[0]
cli_config_path = os.path.join(repo, 'CLI', 'cli_config.json')

# Build URI regex, requires http or https followed by domain or IP
# Accepts optional subdomains, ports, and subpaths
ip_regex = (
    r'((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}'
    r'(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)'
)
domain_regex = (r'([a-zA-Z0-9-]+\.)+[a-zA-Z]{2,6}')
port_regex = (r'(:[0-9]{1,5})?')
path_regex = (r'(/[^\s]*)?')
uri_regex = re.compile(
    r'^(http|https)://'
    r'(' + ip_regex + '|' + domain_regex + ')' + port_regex + path_regex + '$'
)


def is_device_or_sensor(string):
    '''Returns True if arg starts with "device" or "sensor", otherwise False'''
    return (string.startswith("device") or string.startswith("sensor"))


def is_device(string):
    '''Returns True if arg starts with "device", otherwise False'''
    return string.startswith("device")


def is_sensor(string):
    '''Returns True if arg starts with "sensor", otherwise False'''
    return string.startswith("sensor")


def is_int(num):
    '''Returns True if argument is integer, otherwise False'''
    try:
        int(num)
        return True
    except (ValueError, TypeError):
        return False


def is_float(num):
    '''Returns True if argument is float, otherwise False'''
    try:
        float(num)
        return True
    except (ValueError, TypeError):
        return False


def is_int_or_float(num):
    '''Returns True if argument is integer or float, otherwise False'''
    return is_int(num) or is_float(num)


def get_cli_config_name(friendly_name):
    '''Coverts friendly_name to format used in cli_config.json'''
    return friendly_name.lower().replace(" ", "-")


def get_config_filename(friendly_name):
    '''Takes friendly_name, returns lowercase with no spaces and json extension'''
    filename = get_cli_config_name(friendly_name)
    if not filename.endswith('.json'):
        filename += '.json'
    return filename


def get_config_filepath(friendly_name):
    '''Takes friendly_name, returns path to config file. Does not check if file
    exists, can be used to get path for new file or to find an existing file.
    '''
    filename = get_config_filename(friendly_name)
    return os.path.join(get_cli_config()['config_directory'], filename)


def load_node_config_file(friendly_name):
    '''Takes friendly_name of existing node, reads matching config file in
    config_directory (set in cli_config.json), returns contents.
    '''
    config_filepath = get_config_filepath(friendly_name)
    if not os.path.exists(config_filepath):
        raise FileNotFoundError
    with open(config_filepath, 'r', encoding='utf-8') as file:
        config = json.load(file)
    return config


def save_node_config_file(config):
    '''Takes config file dict, generates filename from config.metadata.id,
    creates or overwrites file in config_directory (set in cli_config.json).
    '''
    try:
        config_filepath = get_config_filepath(config['metadata']['id'])
        with open(config_filepath, 'w', encoding='utf-8') as file:
            json.dump(config, file)
        return config_filepath
    except KeyError as exception:
        raise ValueError('config file has no name') from exception


def get_config_param_list(config, param):
    '''Takes config file and name of param that exists in subsections.
    Returns list of values for each occurence of the param name.
    '''
    return [value[param] for key, value in config.items() if param in value]


def valid_ip(ip):
    '''Returns True if arg matches IPv4 regex, otherwise False'''
    return bool(re.match(
        r'^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$',
        ip
    ))


def valid_uri(uri):
    '''Returns True if arg is a valid URI, otherwise False.'''
    return bool(uri_regex.match(uri))


def valid_timestamp(timestamp):
    '''Returns True if arg matches HH:MM timestamp regex, otherwise False'''
    return bool(re.match(r'^([0-1][0-9]|2[0-3]):[0-5][0-9]$', timestamp))


def get_cli_config():
    '''Returns contents of cli_config.json loaded into dict.
    If file does not exist returns template with default values.
    '''
    try:
        with open(cli_config_path, 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        print("Warning: Unable to find cli_config.json, friendly names will not work")
        return {
            'nodes': {},
            'schedule_keywords': {},
            'webrepl_password': 'password',
            'config_directory': os.path.join(repo, 'config_files')
        }


def add_node_to_cli_config(friendly_name, ip):
    '''Takes node friendly_name and IP.
    Adds (or overwrites) entry in nodes section of cli_config.json.
    '''

    # Remove spaces (breaks CLI tool bash completion)
    name = get_cli_config_name(friendly_name)

    # Add to nodes section with cli-safe name as key, IP as value
    cli_config = get_cli_config()
    cli_config['nodes'][name] = ip
    write_cli_config(cli_config)

    # If django backend configured add new node to database
    if 'django_backend' in cli_config:
        print('Uploading node to django database...')
        requests.post(
            f'{cli_config["django_backend"]}/add_node',
            json.dumps({
                'ip': ip,
                'config': load_node_config_file(friendly_name)
            }),
            timeout=5
        )
        print('Done.')


def remove_node_from_cli_config(friendly_name):
    '''Takes node friendly name, deletes from cli_config.json'''

    # Remove spaces (breaks CLI tool bash completion)
    name = get_cli_config_name(friendly_name)

    try:
        cli_config = get_cli_config()
        del cli_config['nodes'][name]
        write_cli_config(cli_config)
    except KeyError:
        pass


def write_cli_config(config):
    '''Takes dict, overwrites cli_config.json'''
    with open(cli_config_path, 'w', encoding='utf-8') as file:
        json.dump(config, file, indent=4)


def get_schedule_keywords_dict():
    '''Returns dict with schedule keywords as keys, timestamps as values.
    Reads from django database if SMARTHOME_FRONTEND env var exists.
    Otherwise reads from CLI/cli_config.json.
    '''

    # Load from django database if env var set
    if os.environ.get('SMARTHOME_FRONTEND'):
        # pylint: disable-next=import-outside-toplevel
        from node_configuration.models import ScheduleKeyword
        return {keyword.keyword: keyword.timestamp
                for keyword in ScheduleKeyword.objects.all()}

    # Load from config file on disk
    config = get_cli_config()
    return config['schedule_keywords']


def get_existing_nodes():
    '''Returns nodes section from cli_config.json as dict.
    Contains all existing node friendly names as keys, sub-dict with IP and
    path to config file as values.
    '''
    config = get_cli_config()
    return config['nodes']


def load_unit_test_config():
    '''Returns config file used in unit tests'''
    path = os.path.join(util, 'unit-test-config.json')
    with open(path, encoding='utf-8') as file:
        return json.load(file)


def get_device_and_sensor_metadata():
    '''Returns dict with devices and sensors keys, each containing dict with
    config_name as keys and metadata file contents as values.
    Dict is built by iterating current device and sensor metadata files.
    '''

    metadata = {'devices': {}, 'sensors': {}}

    # Resolve paths to devices/metadata/ and sensors/metadata/
    device_metadata = os.path.join(repo, 'devices', 'metadata')
    sensor_metadata = os.path.join(repo, 'sensors', 'metadata')

    # Load each device metadata and add to output object
    for i in os.listdir(device_metadata):
        with open(os.path.join(device_metadata, i), 'r', encoding='utf-8') as file:
            params = json.load(file)
            metadata['devices'][params['config_name']] = params

    # Load each sensor metadata and add to output object
    for i in os.listdir(sensor_metadata):
        with open(os.path.join(sensor_metadata, i), 'r', encoding='utf-8') as file:
            params = json.load(file)
            metadata['sensors'][params['config_name']] = params

    return metadata


def celsius_to_fahrenheit(celsius):
    '''Takes temperature in celsius, returns in fahrenheit'''
    return celsius * 1.8 + 32


def celsius_to_kelvin(celsius):
    '''Takes temperature in celsius, returns in kelvin'''
    return celsius + 273.15


def fahrenheit_to_celsius(fahrenheit):
    '''Takes temperature in fahrenheit, returns in celsius'''
    return (fahrenheit - 32) * 5 / 9


def kelvin_to_celsius(kelvin):
    '''Takes temperature in kelvin, returns in celsius'''
    return kelvin - 273.15


def convert_celsius_temperature(celsius, units):
    '''Takes temperature in celsius and desired units, returns in desired units'''
    if units == 'fahrenheit':
        return celsius_to_fahrenheit(celsius)
    if units == 'kelvin':
        return celsius_to_kelvin(celsius)
    raise ValueError(f'Received invalid units ({units})')
