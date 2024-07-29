import re
import os
import json


# Get full path to repository root directory
util = os.path.dirname(os.path.realpath(__file__))
repo = os.path.split(util)[0]


# Returns True if arg starts with "device" or "sensor", otherwise False
def is_device_or_sensor(string):
    return (string.startswith("device") or string.startswith("sensor"))


# Returns True if arg starts with "device", otherwise False
def is_device(string):
    return string.startswith("device")


# Returns True if arg starts with "sensor", otherwise False
def is_sensor(string):
    return string.startswith("sensor")


# Returns True if argument is integer, otherwise False
def is_int(num):
    try:
        int(num)
        return True
    except (ValueError, TypeError):
        return False


# Returns True if argument is float, otherwise False
def is_float(num):
    try:
        float(num)
        return True
    except (ValueError, TypeError):
        return False


# Returns True if argument is integer or float, otherwise False
def is_int_or_float(num):
    if is_int(num) or is_float(num):
        return True
    else:
        return False


# Coverts friendly_name to format used in cli_config.json
def get_cli_config_name(friendly_name):
    return friendly_name.lower().replace(" ", "-")


# Takes friendly_name, returns lowercase with no spaces and json extension
def get_config_filename(friendly_name):
    filename = get_cli_config_name(friendly_name)
    if not filename.endswith('.json'):
        filename += '.json'
    return filename


# Takes config file, param
def get_config_param_list(config, param):
    return [value[param] for key, value in config.items() if param in value]


# Returns True if arg matches IPv4 regex, otherwise False
def valid_ip(ip):
    return bool(re.match(
        r'^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$',
        ip
    ))


# Returns True if arg matches HH:MM timestamp regex, otherwise False
def valid_timestamp(timestamp):
    return bool(re.match(r'^([0-1][0-9]|2[0-3]):[0-5][0-9]$', timestamp))


# Returns contents of cli_config.json loaded into dict
# If file does not exist returns template with default values
def get_cli_config():
    try:
        with open(os.path.join(repo, 'CLI', 'cli_config.json'), 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        print("Warning: Unable to find cli_config.json, friendly names will not work")
        return {
            'nodes': {},
            'schedule_keywords': {},
            'webrepl_password': 'password',
            'config_directory': os.path.join(repo, 'config_files')
        }


# Takes node friendly_name, config abs path, and IP of existing node
# Adds (or overwrites) entry in nodes section of cli_config.json
def add_node_to_cli_config(friendly_name, config_path, ip):
    # Remove spaces (breaks CLI tool bash completion)
    name = get_cli_config_name(friendly_name)

    cli_config = get_cli_config()
    cli_config['nodes'][name] = {
        'config': os.path.abspath(config_path),
        'ip': ip
    }
    write_cli_config(cli_config)


# Takes node friendly name, deletes from cli_config.json
def remove_node_from_cli_config(friendly_name):
    # Remove spaces (breaks CLI tool bash completion)
    name = get_cli_config_name(friendly_name)

    try:
        cli_config = get_cli_config()
        del cli_config['nodes'][name]
        write_cli_config(cli_config)
    except KeyError:
        pass


# Takes dict, overwrites cli_config.json
def write_cli_config(config):
    with open(os.path.join(repo, 'CLI', 'cli_config.json'), 'w') as file:
        json.dump(config, file)


# Returns dict with schedule keywords as keys, timestamps as values
# Reads from django database if argument is passed
# Otherwise reads from CLI/cli_config.json
def get_schedule_keywords_dict(django=False):
    # Load from SQL
    if os.environ.get('SMARTHOME_FRONTEND'):
        from node_configuration.models import ScheduleKeyword
        return {keyword.keyword: keyword.timestamp
                for keyword in ScheduleKeyword.objects.all()}

    # Load from config file on disk
    else:
        config = get_cli_config()
        return config['schedule_keywords']


# Returns nodes section from cli_config.json as dict
# Contains section for each existing node with friendly name
# as key, sub-dict with IP and path to config file as value
def get_existing_nodes():
    config = get_cli_config()
    return config['nodes']


# Returns config file used in unit tests
def load_unit_test_config():
    with open(os.path.join(util, 'unit-test-config.json')) as file:
        return json.load(file)


# Reads all device and sensor metadata files
# Returns dict with devices and sensors keys, each containing list of metadata objects
def get_device_and_sensor_metadata():
    metadata = {'devices': [], 'sensors': []}

    # Resolve paths to devices/metadata/ and sensors/metadata/
    util = os.path.dirname(os.path.realpath(__file__))
    repo = os.path.split(util)[0]
    device_metadata = os.path.join(repo, 'devices', 'metadata')
    sensor_metadata = os.path.join(repo, 'sensors', 'metadata')

    # Load each device metadata and add to output object
    for i in os.listdir(device_metadata):
        with open(os.path.join(device_metadata, i), 'r') as file:
            metadata['devices'].append(json.load(file))

    # Load each sensor metadata and add to output object
    for i in os.listdir(sensor_metadata):
        with open(os.path.join(sensor_metadata, i), 'r') as file:
            metadata['sensors'].append(json.load(file))

    return metadata


# Takes temperature in celsius, returns in fahrenheit
def celsius_to_fahrenheit(celsius):
    return celsius * 1.8 + 32


# Takes temperature in celsius, returns in kelvin
def celsius_to_kelvin(celsius):
    return celsius + 273.15


# Takes temperature in fahrenheit, returns in celsius
def fahrenheit_to_celsius(fahrenheit):
    return (fahrenheit - 32) * 5 / 9


# Takes temperature in kelvin, returns in celsius
def kelvin_to_celsius(kelvin):
    return kelvin - 273.15


# Takes temperature in celsius and desired units, returns in desired units
def convert_celsius_temperature(celsius, units):
    if units == 'fahrenheit':
        return celsius_to_fahrenheit(celsius)
    elif units == 'kelvin':
        return celsius_to_kelvin(celsius)
