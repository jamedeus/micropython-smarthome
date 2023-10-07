from helper_functions import get_device_and_sensor_metadata

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
        "floor": "",
        "schedule_keywords": ""
    },
    "wifi": {
        "ssid": "",
        "password": ""
    }
}


# Returns dict containing config templates for all device and sensor types
# Devices are in "device" subsection, keyed by classname
# Sensors are in "sensor" subsection, keyed by classname
def build_config_templates():
    config_templates = {
        "device": {},
        "sensor": {}
    }

    # Get object containing all device and sensor metadata objects
    metadata = get_device_and_sensor_metadata()

    # Iterate device metadata files, add each config template lists to dict
    for i in metadata['devices']:
        config_templates['device'][i['class_name']] = i['config_template']

    # Iterate sensor metadata files, add each config template lists to dict
    for i in metadata['sensors']:
        config_templates['sensor'][i['class_name']] = i['config_template']

    return config_templates


# Combine config templates from all device and sensor metadata files
config_templates = build_config_templates()


# Options for each supported IR Blaster target device, used to populate ApiTarget menu
ir_blaster_options = {
    "tv": ['power', 'vol_up', 'vol_down', 'mute', 'up', 'down', 'left', 'right', 'enter', 'settings', 'exit', 'source'],
    "ac": ['start', 'stop', 'off']
}


# API endpoints supported with device as target instance
# Used to populate options for ApiTarget rules
device_endpoints = ['enable', 'disable', 'enable_in', 'disable_in', 'set_rule', 'reset_rule', 'turn_on', 'turn_off']


# API endpoints supported with sensor as target instance
# Used to populate options for ApiTarget rules
sensor_endpoints = ['enable', 'disable', 'enable_in', 'disable_in', 'set_rule', 'reset_rule', 'trigger_sensor']
