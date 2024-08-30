'''Contains functions used to validate ESP32 config files'''

from instance_validators import validate_rules
from helper_functions import (
    is_device_or_sensor,
    is_device,
    is_sensor,
    get_config_param_list,
    valid_ip,
    valid_uri
)
from validation_constants import (
    valid_device_pins,
    valid_sensor_pins,
    config_templates,
    valid_config_keys,
    ir_blaster_options
)

# Create generators by parsing device and sensor types from templates
valid_device_types = ([config_templates['device'][i]['_type']
                      for i in config_templates['device']])
valid_sensor_types = ([config_templates['sensor'][i]['_type']
                      for i in config_templates['sensor']])


def validate_instance_types(config):
    '''Accepts completed config dict, returns True if all device and sensor
    types are valid, returns error string if one or more are invalid.
    '''

    # Get device and sensor IDs
    devices = [key for key in config if is_device(key)]
    sensors = [key for key in config if is_sensor(key)]

    # Get device and sensor types
    device_types = [config[device]['_type'] for device in devices]
    sensor_types = [config[sensor]['_type'] for sensor in sensors]

    # Check for invalid device/sensor types
    for dtype in device_types:
        if dtype not in valid_device_types:
            return f'Invalid device type {dtype} used'

    for stype in sensor_types:
        if stype not in valid_sensor_types:
            return f'Invalid sensor type {stype} used'

    return True


def validate_instance_pins(config):
    '''Accepts completed config dict, returns True if all device and sensor
    pins are valid, returns error string if one or more are invalid.
    '''

    # Get device and sensor pins
    try:
        device_pins = [int(val['pin']) for key, val in config.items()
                       if is_device(key) and 'pin' in val]
        sensor_pins = [int(val['pin']) for key, val in config.items()
                       if is_sensor(key) and 'pin' in val]
    except ValueError:
        return 'Invalid pin (non-integer)'

    # Check for invalid pins (reserved, input-only, etc)
    for pin in device_pins:
        if str(pin) not in valid_device_pins:
            return f'Invalid device pin {pin} used'

    for pin in sensor_pins:
        if str(pin) not in valid_sensor_pins:
            return f'Invalid sensor pin {pin} used'

    return True


def validate_config_keys(config, valid_keys):
    '''Accepts completed config dict and template with all required config keys
    (see validation_constants.valid_config_keys). Returns True if all required
    keys exist, returns error string if one or more keys are missing.
    '''
    for key in valid_keys:
        if key not in config:
            return f"Missing required top-level {key} key"
        if isinstance(valid_keys[key], dict):
            if validate_config_keys(config[key], valid_keys[key]) is not True:
                return f"Missing required key in {key} section"
    return True


def validate_ir_blaster_section(section):
    '''Takes ir_blaster section (dict) from config files, returns True if all
    requried keys are present, pin is valid, and targets are valid.
    '''
    if "target" not in section:
        return "Missing required target key"
    if "pin" not in section:
        return "Missing required pin key"
    if str(section["pin"]) not in valid_device_pins:
        return f'Invalid ir_blaster pin {section["pin"]} used'
    for i in section['target']:
        if i not in ir_blaster_options:
            return f'Invalid IR target {i}'
    return True


def validate_full_config(config):
    '''Accepts completed config dict, validates syntax, returns True if valid,
    returns error string with failure reason if invalid. If multiple syntax
    errors exist the error string will only describe the first error.
    '''

    # Confirm config has all required keys (see valid_config_keys)
    valid = validate_config_keys(config, valid_config_keys)
    if valid is not True:
        return valid

    # Floor must be integer
    try:
        int(config['metadata']['floor'])
    except ValueError:
        return 'Invalid floor, must be integer'

    # Get list of all nicknames, check for duplicates
    nicknames = get_config_param_list(config, 'nickname')
    if len(nicknames) != len(set(nicknames)):
        return 'Contains duplicate nicknames'

    # Get list of all pins, check for duplicates
    pins = get_config_param_list(config, 'pin')
    if len(pins) != len(set(pins)):
        return 'Contains duplicate pins'

    # Check if all device and sensor types are valid
    valid = validate_instance_types(config)
    if valid is not True:
        return valid

    # Check if all device and sensor pins are valid
    valid = validate_instance_pins(config)
    if valid is not True:
        return valid

    # Check if all IP addresses are valid
    ips = [value['ip'] for key, value in config.items() if 'ip' in value]
    for ip in ips:
        if not valid_ip(ip):
            return f'Invalid IP {ip}'

    # Check if all URI addresses are valid
    uris = [value['uri'] for key, value in config.items() if 'uri' in value]
    for uri in uris:
        if not valid_uri(uri):
            return f'Invalid URI {uri}'

    # Validate rules for all devices and sensors
    for instance in [key for key in config.keys() if is_device_or_sensor(key)]:
        valid = validate_rules(config[instance])
        if valid is not True:
            print(f"\nERROR: {valid}\n")
            return valid

    # Validate ir_blaster section if present
    if 'ir_blaster' in config:
        valid = validate_ir_blaster_section(config['ir_blaster'])
        if valid is not True:
            return valid

    return True
