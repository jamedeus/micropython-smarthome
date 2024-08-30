'''Contains constants with config section templates for each supported device
and sensor type, constants with acceptable values for config parameters, etc.
'''

from helper_functions import get_device_and_sensor_metadata, get_ir_blaster_keys_map

# All valid ESP32 pins, excluding input-only
valid_device_pins = (
    '4',
    '13',
    '16',
    '17',
    '18',
    '19',
    '21',
    '22',
    '23',
    '25',
    '26',
    '27',
    '32',
    '33'
)


# All valid ESP32 pins, including input-only
valid_sensor_pins = (
    '4',
    '5',
    '13',
    '14',
    '15',
    '16',
    '17',
    '18',
    '19',
    '21',
    '22',
    '23',
    '25',
    '26',
    '27',
    '32',
    '33',
    '34',
    '35',
    '36',
    '39'
)


# Required keys for all config files
valid_config_keys = {
    "metadata": {
        "id": "",
        "location": "",
        "floor": 0,
        "schedule_keywords": {}
    }
}


def build_config_templates():
    '''Returns dict containing config templates for all device and sensor types
    Devices are in "device" subsection, keyed by classname
    Sensors are in "sensor" subsection, keyed by classname
    '''

    output = {
        "device": {},
        "sensor": {}
    }

    # Get dict with contents of all device and sensor metadata files
    metadata = get_device_and_sensor_metadata()

    # Iterate device metadata, add each config template to dict
    for i in metadata['devices'].values():
        output['device'][i['display_name']] = i['config_template']

    # Iterate sensor metadata, add each config template to dict
    for i in metadata['sensors'].values():
        output['sensor'][i['display_name']] = i['config_template']

    return output


# Combine config templates from all device and sensor metadata files
config_templates = build_config_templates()


# Mapping dict with IR Blaster target names as key, list IR key names as value
# Used to populate ApiTarget menu, api_client menu options, etc
ir_blaster_options = get_ir_blaster_keys_map()


# API endpoints supported with device as target instance
# Used to populate options for ApiTarget rules
device_endpoints = [
    'enable',
    'disable',
    'enable_in',
    'disable_in',
    'set_rule',
    'reset_rule',
    'turn_on',
    'turn_off'
]


# API endpoints supported with sensor as target instance
# Used to populate options for ApiTarget rules
sensor_endpoints = [
    'enable',
    'disable',
    'enable_in',
    'disable_in',
    'set_rule',
    'reset_rule',
    'trigger_sensor'
]
