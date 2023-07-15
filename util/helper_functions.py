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


# Takes config file, param
def get_config_param_list(config, param):
    return [value[param] for key, value in config.items() if param in value]


# Returns True if arg matches IPv4 regex, otherwise False
def valid_ip(ip):
    return bool(re.match(r'^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$', ip))


# Returns True if arg matches HH:MM timestamp regex, otherwise False
def valid_timestamp(timestamp):
    return bool(re.match(r'^([0-1][0-9]|2[0-3]):[0-5][0-9]$', timestamp))


# Read current schedule keywords from config file
def get_schedule_keywords_dict(django=False):
    # Load from SQL
    if os.environ.get('SMARTHOME_FRONTEND'):
        from node_configuration.models import ScheduleKeyword
        return {keyword.keyword: keyword.timestamp for keyword in ScheduleKeyword.objects.all()}

    # Load from config file on disk
    else:
        try:
            with open(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'schedule-keywords.json'), 'r') as file:
                return json.load(file)
        except FileNotFoundError:
            return {}


# Load nodes.json from disk and return as dict
# Contains section for each existing node with friendly name
# as key, sub-dict with IP and path to config file as value
def get_existing_nodes():
    try:
        with open(os.path.join(repo, 'CLI', 'nodes.json'), 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        return {}
