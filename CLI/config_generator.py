#!/usr/bin/python3

import json
import questionary
from questionary import Validator, ValidationError
from helper_functions import valid_ip


output_template = {
    'metadata': {
        'id': '',
        'floor': '',
        'location': ''
    },
    'wifi': {
        'ssid': '',
        'password': ''
    }
}

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

# Map int rule limits to device/sensor types
rule_limits = {
    'dimmer': (1, 100),
    'bulb': (1, 100),
    'pwm': (0, 1023),
    'wled': (1, 255),
    'pir': (0, 60),
    'si7021': (65, 80),
}

templates = {
    "device": {
        "Dimmer": {
            "_type": "dimmer",
            "nickname": "placeholder",
            "ip": "placeholder",
            "min_bright": "placeholder",
            "max_bright": "placeholder",
            "default_rule": "placeholder",
            "schedule": {}
        },

        "Bulb": {
            "_type": "bulb",
            "nickname": "placeholder",
            "ip": "placeholder",
            "min_bright": "placeholder",
            "max_bright": "placeholder",
            "default_rule": "placeholder",
            "schedule": {}
        },

        "Relay": {
            "_type": "relay",
            "nickname": "placeholder",
            "ip": "placeholder",
            "default_rule": "placeholder",
            "schedule": {}
        },

        "DumbRelay": {
            "_type": "dumb-relay",
            "nickname": "placeholder",
            "default_rule": "placeholder",
            "pin": "placeholder",
            "schedule": {}
        },

        "DesktopTarget": {
            "_type": "desktop",
            "nickname": "placeholder",
            "ip": "placeholder",
            "default_rule": "placeholder",
            "schedule": {}
        },

        "LedStrip": {
            "_type": "pwm",
            "nickname": "placeholder",
            "default_rule": "placeholder",
            "min_bright": "placeholder",
            "max_bright": "placeholder",
            "pin": "placeholder",
            "schedule": {}
        },

        "Mosfet": {
            "_type": "mosfet",
            "nickname": "placeholder",
            "default_rule": "placeholder",
            "pin": "placeholder",
            "schedule": {}
        },

        "ApiTarget": {
            "_type": "api-target",
            "nickname": "placeholder",
            "ip": "placeholder",
            "default_rule": "placeholder",
            "schedule": {}
        },

        "Wled": {
            "_type": "wled",
            "nickname": "placeholder",
            "ip": "placeholder",
            "default_rule": "placeholder",
            "min_bright": "placeholder",
            "max_bright": "placeholder",
            "schedule": {}
        },
    },

    "sensor": {
        "MotionSensor": {
            "_type": "pir",
            "nickname": "placeholder",
            "pin": "placeholder",
            "default_rule": "placeholder",
            "targets": [],
            "schedule": {}
        },

        "DesktopTrigger": {
            "_type": "desktop",
            "nickname": "placeholder",
            "ip": "placeholder",
            "default_rule": "placeholder",
            "targets": [],
            "schedule": {}
        },

        "Thermostat": {
            "_type": "si7021",
            "nickname": "placeholder",
            "default_rule": "placeholder",
            "mode": "placeholder",
            "tolerance": "placeholder",
            "targets": [],
            "schedule": {}
        },

        "Dummy": {
            "_type": "dummy",
            "nickname": "placeholder",
            "default_rule": "placeholder",
            "targets": [],
            "schedule": {}
        },

        "Switch": {
            "_type": "switch",
            "nickname": "placeholder",
            "pin": "placeholder",
            "default_rule": "placeholder",
            "targets": [],
            "schedule": {}
        }
    }
}


class IntRange(Validator):
    def __init__(self, minimum, maximum):
        self.minimum = int(minimum)
        self.maximum = int(maximum)

    def validate(self, document):
        if validate_int(document.text) and self.minimum <= int(document.text) <= self.maximum:
            return True
        else:
            raise ValidationError(
                message=f"Must be int between {self.minimum} and {self.maximum}",
                cursor_position=len(document.text)
            )


def validate_int(num):
    try:
        int(num)
        return True
    except (ValueError, TypeError):
        return False


def validate_float(num):
    try:
        float(num)
        return True
    except (ValueError, TypeError):
        return False


def validate_int_or_float(num):
    if validate_int(num) or validate_float(num):
        return True
    else:
        return False


def metadata_prompt():
    name = questionary.text("Enter a descriptive name for this node").ask()
    floor = questionary.text("Enter floor number", validate=validate_int).ask()
    location = questionary.text("Enter a brief description of the node's physical location").ask()

    return {
        'id': name,
        'floor': floor,
        'location': location
    }


def wifi_prompt():
    ssid = questionary.text("Enter wifi SSID (2.4 GHz only)").ask()
    password = questionary.password("Enter wifi password").ask()

    return {
        'ssid': ssid,
        'password': password
    }


def sensor_type():
    return questionary.select(
        "Select sensor type",
        choices=list(templates['sensor'].keys())
    ).ask()


def device_type():
    return questionary.select(
        "Select device type",
        choices=list(templates['device'].keys())
    ).ask()


def configure_device():
    config = templates['device'][device_type()].copy()
    _type = config['_type']

    for i in [i for i in config if config[i] == "placeholder"]:
        if i == "nickname":
            config[i] = questionary.text("Enter a memorable nickname for the device").ask()
        elif i == "pin":
            config[i] = questionary.select("Select pin", choices=valid_device_pins).ask()
        elif i == "default_rule":
            if _type in ['dimmer', 'bulb', 'pwm', 'wled']:
                config[i] = default_rule_prompt_int_option(_type)
            else:
                config[i] = questionary.select("Enter default rule", choices=['Enabled', 'Disabled']).ask()
        elif i == "min_bright":
            config[i] = questionary.text("Enter minimum brightness", validate=IntRange(*rule_limits[_type])).ask()
        elif i == "max_bright":
            config[i] = questionary.text("Enter maximum brightness", validate=IntRange(*rule_limits[_type])).ask()
        elif i == "ip":
            config[i] = questionary.text("Enter IP address", validate=valid_ip).ask()

    return config


def configure_sensor():
    config = templates['sensor'][sensor_type()].copy()
    _type = config['_type']

    for i in [i for i in config if config[i] == "placeholder"]:
        if i == "nickname":
            config[i] = questionary.text("Enter a memorable nickname for the sensor").ask()
        elif i == "pin":
            config[i] = questionary.select("Select pin", choices=valid_sensor_pins).ask()
        elif i == "default_rule":
            if _type in ['pir', 'si7021']:
                config[i] = default_rule_prompt_int_option(_type)
            elif _type == 'dummy':
                config[i] = questionary.select("Enter default rule", choices=['Enabled', 'Disabled', 'On', 'Off']).ask()
            else:
                config[i] = questionary.select("Enter default rule", choices=['Enabled', 'Disabled']).ask()
        elif i == "ip":
            config[i] = questionary.text("Enter IP address", validate=valid_ip).ask()
        elif i == "mode":
            config[i] = questionary.select("Select mode", choices=['cool', 'heat']).ask()
        elif i == "tolerance":
            config[i] = questionary.text("Enter temperature tolerance", validate=validate_int_or_float).ask()

    return config


def default_rule_prompt_int_option(_type):
    choice = questionary.select("Select default rule", choices=['Enabled', 'Disabled', 'Int']).ask()
    if choice == 'Int':
        return questionary.text("Enter default rule", validate=IntRange(*rule_limits[_type])).ask()
    else:
        return choice


if __name__ == '__main__':
    # Add output of metadata + wifi prompts to template
    config = output_template.copy()
    config['metadata'].update(metadata_prompt())
    config['wifi'].update(wifi_prompt())

    # Lists to store + count device and sensor sections
    devices = []
    sensors = []

    # Add output of device and sensor prompts to lists
    while True:
        choice = questionary.select("\nAdd instances?", choices=['device', 'sensor', 'done']).ask()
        if choice == 'device':
            devices.append(configure_device())
        elif choice == 'sensor':
            sensors.append(configure_sensor())
        elif choice == 'done':
            break

    # Add sequential device and sensor keys (device1, device2, etc)
    # for each item in devices and sensors
    for index, instance in enumerate(devices, 1):
        config[f'device{index}'] = instance
    for index, instance in enumerate(sensors, 1):
        config[f'sensor{index}'] = instance

    print(json.dumps(config, indent=4))
