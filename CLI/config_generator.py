#!/usr/bin/python3

import json
import questionary
from questionary import Validator, ValidationError
from helper_functions import valid_ip, valid_timestamp, is_device, is_sensor, is_device_or_sensor

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


class GenerateConfigFile:
    def __init__(self):
        self.config = {
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

        # List of pins that have already been used, prevent duplicates
        self.used_pins = []
        self.used_nicknames = []

        # Prompt user to enter metadata and wifi credentials
        self.metadata_prompt()
        self.wifi_prompt()

        # Prompt user to add devices and sensors
        self.add_devices_and_sensors()

        # Prompt user to select targets for each sensor
        self.select_sensor_targets()

        # Prompt user to add schedule rules for each device and sensor
        self.schedule_rules_prompt()

    # Return True if nickname unique, False if already in self.used_nicknames
    def unique_nickname(self, nickname):
        return nickname not in self.used_nicknames

    def add_devices_and_sensors(self):
        # Lists to store + count device and sensor sections
        devices = []
        sensors = []

        # Add output of device and sensor prompts to lists
        while True:
            choice = questionary.select("\nAdd instances?", choices=['device', 'sensor', 'done']).ask()
            if choice == 'device':
                devices.append(self.configure_device())
            elif choice == 'sensor':
                sensors.append(self.configure_sensor())
            elif choice == 'done':
                break

        # Add sequential device and sensor keys (device1, device2, etc)
        # for each item in devices and sensors
        for index, instance in enumerate(devices, 1):
            self.config[f'device{index}'] = instance
        for index, instance in enumerate(sensors, 1):
            self.config[f'sensor{index}'] = instance

    def metadata_prompt(self):
        name = questionary.text("Enter a descriptive name for this node").ask()
        floor = questionary.text("Enter floor number", validate=validate_int).ask()
        location = questionary.text("Enter a brief description of the node's physical location").ask()

        self.config['metadata'].update({'id': name, 'floor': floor, 'location': location})

    def wifi_prompt(self):
        ssid = questionary.text("Enter wifi SSID (2.4 GHz only)").ask()
        password = questionary.password("Enter wifi password").ask()

        self.config['wifi'].update({'ssid': ssid, 'password': password})

    def sensor_type(self):
        return questionary.select(
            "Select sensor type",
            choices=list(templates['sensor'].keys())
        ).ask()

    def device_type(self):
        return questionary.select(
            "Select device type",
            choices=list(templates['device'].keys())
        ).ask()

    def configure_device(self):
        config = templates['device'][self.device_type()].copy()
        _type = config['_type']

        for i in [i for i in config if config[i] == "placeholder"]:
            if i == "nickname":
                nickname = questionary.text(
                    "Enter a memorable nickname for the device",
                    validate=self.unique_nickname
                ).ask()
                self.used_nicknames.append(nickname)
                config[i] = nickname
            elif i == "pin":
                # Remove already used pins from choices to prevent duplicates
                choices = [pin for pin in valid_device_pins if pin not in self.used_pins]
                pin = questionary.select("Select pin", choices=choices).ask()
                self.used_pins.append(pin)
                config[i] = pin
            elif i == "default_rule":
                config[i] = self.rule_prompt_router(_type)
            elif i == "min_bright":
                config[i] = questionary.text("Enter minimum brightness", validate=IntRange(*rule_limits[_type])).ask()
            elif i == "max_bright":
                config[i] = questionary.text("Enter maximum brightness", validate=IntRange(*rule_limits[_type])).ask()
            elif i == "ip":
                config[i] = questionary.text("Enter IP address", validate=valid_ip).ask()

        return config

    def configure_sensor(self):
        config = templates['sensor'][self.sensor_type()].copy()
        _type = config['_type']

        for i in [i for i in config if config[i] == "placeholder"]:
            if i == "nickname":
                nickname = questionary.text(
                    "Enter a memorable nickname for the sensor",
                    validate=self.unique_nickname
                ).ask()
                self.used_nicknames.append(nickname)
                config[i] = nickname
            elif i == "pin":
                # Remove already used pins from choices to prevent duplicates
                choices = [pin for pin in valid_sensor_pins if pin not in self.used_pins]
                pin = questionary.select("Select pin", choices=choices).ask()
                self.used_pins.append(pin)
                config[i] = pin
            elif i == "default_rule":
                config[i] = self.rule_prompt_router(_type)
            elif i == "ip":
                config[i] = questionary.text("Enter IP address", validate=valid_ip).ask()
            elif i == "mode":
                config[i] = questionary.select("Select mode", choices=['cool', 'heat']).ask()
            elif i == "tolerance":
                config[i] = questionary.text("Enter temperature tolerance", validate=validate_int_or_float).ask()

        return config

    def rule_prompt_router(self, _type):
        if _type in ['dimmer', 'bulb', 'pwm', 'wled', 'pir', 'si7021']:
            return self.default_rule_prompt_int_option(_type)
        elif _type == 'dummy':
            return questionary.select("Enter default rule", choices=['Enabled', 'Disabled', 'On', 'Off']).ask()
        else:
            return questionary.select("Enter default rule", choices=['Enabled', 'Disabled']).ask()

    def default_rule_prompt_int_option(self, _type):
        choice = questionary.select("Select default rule", choices=['Enabled', 'Disabled', 'Int']).ask()
        if choice == 'Int':
            return questionary.text("Enter default rule", validate=IntRange(*rule_limits[_type])).ask()
        else:
            return choice

    def select_sensor_targets(self):
        print("\nSelect target devices for each sensor")
        print("All targets will turn on when the sensor is activated")
        # Get list of all sensor IDs
        sensors = [key for key in self.config.keys() if is_sensor(key)]

        # Map strings displayed for each device option (syntax: "Nickname (type)") to their IDs
        targets_map = {}
        for key in [key for key in self.config.keys() if is_device(key)]:
            display = f"{self.config[key]['nickname']} ({self.config[key]['_type']})"
            targets_map[display] = key

        # Show checkbox prompt for each sensor with all devices as options
        for sensor in sensors:
            prompt = f"\nSelect targets for {self.config[sensor]['nickname']} ({self.config[sensor]['_type']})"
            targets = questionary.checkbox(prompt, choices=targets_map.keys()).ask()

            # Add selection to config
            for i in targets:
                self.config[sensor]['targets'].append(targets_map[i])

    def add_schedule_rule(self, _type):
        timestamp = questionary.text("Enter timestamp (HH:MM)", validate=valid_timestamp).ask()
        rule = self.rule_prompt_router(_type)
        return timestamp, rule

    def schedule_rules_prompt(self):
        for instance in [key for key in self.config if is_device_or_sensor(key)]:
            prompt = f"\nWould you like to add schedule rules for {self.config[instance]['nickname']}?"
            choice = questionary.select(prompt, choices=['Yes', 'No']).ask()
            if choice == 'Yes':
                while True:
                    timestamp, rule = self.add_schedule_rule(self.config[instance]['_type'])
                    self.config[instance]['schedule'][timestamp] = rule
                    choice = questionary.select("\nAdd another?", choices=['Yes', 'No']).ask()
                    if choice == 'No':
                        break


if __name__ == '__main__':
    config = GenerateConfigFile()
    print(json.dumps(config.config, indent=4))
