from instance_validators import validate_rules
from helper_functions import is_device_or_sensor, is_device, is_sensor, get_config_param_list, valid_ip
from validation_constants import valid_device_pins, valid_sensor_pins, config_templates, valid_config_keys

# Parse tuple of device and sensor types from templates, used in validation
valid_device_types = tuple([config_templates['device'][i]['_type'] for i in config_templates['device'].keys()])
valid_sensor_types = tuple([config_templates['sensor'][i]['_type'] for i in config_templates['sensor'].keys()])


# Accepts completed config, returns True if all device and sensor types are valid, error string if invalid
def validate_instance_types(config):
    # Get device and sensor IDs
    devices = [key for key in config.keys() if is_device(key)]
    sensors = [key for key in config.keys() if is_sensor(key)]

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


# Accepts completed config, returns True if all device and sensor pins are valid, error string if invalid
def validate_instance_pins(config):
    # Get device and sensor pins
    try:
        device_pins = [int(val['pin']) for key, val in config.items() if is_device(key) and 'pin' in val]
        sensor_pins = [int(val['pin']) for key, val in config.items() if is_sensor(key) and 'pin' in val]
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


# Accepts complete config + template with correct keys
# Recursively checks that each template key also exists in config
def validate_config_keys(config, valid_config_keys):
    for key in valid_config_keys:
        if key not in config:
            return f"Missing required top-level {key} key"
        elif isinstance(valid_config_keys[key], dict):
            if validate_config_keys(config[key], valid_config_keys[key]) is not True:
                return f"Missing required key in {key} section"
    return True


# Accepts completed config, return True if valid, error string if invalid
def validate_full_config(config):
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

    # Validate rules for all devices and sensors
    for instance in [key for key in config.keys() if is_device_or_sensor(key)]:
        valid = validate_rules(config[instance])
        if valid is not True:
            print(f"\nERROR: {valid}\n")
            return valid

    return True
