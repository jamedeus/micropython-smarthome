'''Utility functions used by both CLI tools and django backend'''

import re
import os
import json
import importlib.util

# Get full path to repository root directory
util = os.path.dirname(os.path.realpath(__file__))
repo = os.path.split(util)[0]

# Get path to cli_config.json
cli_config_path = os.path.join(repo, 'CLI', 'cli_config.json')

# Get path to IR Blaster codes directory
ir_codes_dir = os.path.join(repo, 'lib', 'ir_codes')

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
    '''Converts friendly_name to format used in cli_config.json'''
    return friendly_name.lower().replace(" ", "-")


def get_config_filename(friendly_name):
    '''Takes friendly_name, returns lowercase with no spaces and json extension'''
    filename = get_cli_config_name(friendly_name)
    if not filename.endswith('.json'):
        filename += '.json'
    return filename


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
    try:
        with open(cli_config_path, 'r', encoding='utf-8') as file:
            config = json.load(file)
            return config['schedule_keywords']
    except FileNotFoundError:
        return {}


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

    # Resolve paths to util/metadata/devices and util/metadata/sensors
    device_metadata = os.path.join(util, 'metadata', 'devices')
    sensor_metadata = os.path.join(util, 'metadata', 'sensors')

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


def get_ir_blaster_keys_map():
    '''Returns dict with IR target names as keys, list of keys as values.
    Used to populate key options lists, validate config files, etc.
    '''

    keys_map = {}

    for i in os.listdir(ir_codes_dir):
        # Get IR target name, path to codes module
        target_name = i.replace('_ir_codes.py', '')
        target_path = os.path.join(ir_codes_dir, i)

        # Get module spec, skip if is not python module
        spec = importlib.util.spec_from_file_location(i, target_path)
        if spec is None:
            continue

        # Import module
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # Add list of key names to output
        target_name = i.replace('_ir_codes.py', '')
        keys_map[target_name] = list(module.codes.keys())

    return keys_map


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
