#!/usr/bin/python3

import json
import questionary
from questionary import Validator, ValidationError
from colorama import Fore
from instance_validators import validate_rules
from validation_constants import valid_device_pins, valid_sensor_pins, config_templates
from helper_functions import (
    valid_ip,
    valid_timestamp,
    is_device,
    is_sensor,
    is_device_or_sensor,
    is_int,
    is_float
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


class IntRange(Validator):
    def __init__(self, minimum, maximum):
        self.minimum = int(minimum)
        self.maximum = int(maximum)

    def validate(self, document):
        if is_int(document.text) and self.minimum <= int(document.text) <= self.maximum:
            return True
        else:
            raise ValidationError(
                message=f"Must be int between {self.minimum} and {self.maximum}",
                cursor_position=len(document.text)
            )


class FloatRange(Validator):
    def __init__(self, minimum, maximum):
        self.minimum = float(minimum)
        self.maximum = float(maximum)

    def validate(self, document):
        if is_float(document.text) and self.minimum <= float(document.text) <= self.maximum:
            return True
        else:
            raise ValidationError(
                message=f"Must be float between {self.minimum} and {self.maximum}",
                cursor_position=len(document.text)
            )


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
        floor = questionary.text("Enter floor number", validate=is_int).ask()
        location = questionary.text("Enter a brief description of the node's physical location").ask()

        self.config['metadata'].update({'id': name, 'floor': floor, 'location': location})

    def wifi_prompt(self):
        ssid = questionary.text("Enter wifi SSID (2.4 GHz only)").ask()
        password = questionary.password("Enter wifi password").ask()

        self.config['wifi'].update({'ssid': ssid, 'password': password})

    def sensor_type(self):
        return questionary.select(
            "Select sensor type",
            choices=list(config_templates['sensor'].keys())
        ).ask()

    def device_type(self):
        return questionary.select(
            "Select device type",
            choices=list(config_templates['device'].keys())
        ).ask()

    # Prompt user to configure a device
    # config arg accepts partially-complete template, used to re-prompt
    # user without repeating all questions after failed validation
    def configure_device(self, config=None):
        if config is None:
            config = config_templates['device'][self.device_type()].copy()
            _type = config['_type']
        # Config previously failed validation, repeat prompt with most options pre-selected
        else:
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
                config[i] = self.default_rule_prompt_router(config)

            elif i == "min_bright":
                config[i] = questionary.text(
                    "Enter minimum brightness",
                    default=str(rule_limits[_type][0]),
                    validate=IntRange(*rule_limits[_type])
                ).ask()

            elif i == "max_bright":
                config[i] = questionary.text(
                    "Enter maximum brightness",
                    default=str(rule_limits[_type][1]),
                    validate=IntRange(config['min_bright'], rule_limits[_type][1])
                ).ask()

            elif i == "ip":
                config[i] = questionary.text("Enter IP address", validate=valid_ip).ask()

        # Confirm all selections are valid
        valid = validate_rules(config)
        if valid is not True:
            # Print error, remove potentially invalid parameters and re-prompt
            print(f'{Fore.RED}ERROR{Fore.RESET}: {valid}')
            print('Resetting relevant options, please try again')
            return self.configure_device(self.reset_config_template(config))
        else:
            return config

    # Prompt user to configure a sensor
    # config arg accepts partially-complete template, used to re-prompt
    # user without repeating all questions after failed validation
    def configure_sensor(self, config=None):
        if config is None:
            config = config_templates['sensor'][self.sensor_type()].copy()

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
                config[i] = self.default_rule_prompt_router(config)

            elif i == "ip":
                config[i] = questionary.text("Enter IP address", validate=valid_ip).ask()

            elif i == "mode":
                config[i] = questionary.select("Select mode", choices=['cool', 'heat']).ask()

            elif i == "tolerance":
                config[i] = questionary.text("Enter temperature tolerance", validate=FloatRange(0, 10)).ask()

        # Confirm all selections are valid
        valid = validate_rules(config)
        if valid is not True:
            # Print error, remove potentially invalid parameters and re-prompt
            print(f'{Fore.RED}ERROR{Fore.RESET}: {valid}')
            print('Resetting relevant options, please try again')
            return self.configure_sensor(self.reset_config_template(config))
        else:
            return config

    # Takes config that failed validation, replaces potentially invalid params
    # with placeholder. Used to re-prompt user without repeating all questions.
    def reset_config_template(self, config):
        for i in config:
            if i not in ['nickname', 'pin', '_type', 'schedule']:
                config[i] = 'placeholder'
        return config

    def default_rule_prompt_router(self, config):
        _type = config['_type']
        if _type in ['dimmer', 'bulb', 'pwm', 'wled']:
            return questionary.text(
                "Enter default rule",
                validate=IntRange(config['min_bright'], config['max_bright'])
            ).ask()
        elif _type in ['pir', 'si7021']:
            return questionary.text("Enter default rule", validate=IntRange(*rule_limits[_type])).ask()
        elif _type == 'dummy':
            return questionary.select("Enter default rule", choices=['On', 'Off']).ask()
        else:
            return questionary.select("Enter default rule", choices=['Enabled', 'Disabled']).ask()

    def schedule_rule_prompt_router(self, config):
        _type = config['_type']
        if _type in ['dimmer', 'bulb', 'pwm', 'wled']:
            return self.rule_prompt_with_int_option(config['min_bright'], config['max_bright'])
        elif _type in ['pir', 'si7021']:
            return self.rule_prompt_with_int_option(*rule_limits[_type])
        elif _type == 'dummy':
            return questionary.select("Enter default rule", choices=['Enabled', 'Disabled', 'On', 'Off']).ask()
        else:
            return questionary.select("Enter default rule", choices=['Enabled', 'Disabled']).ask()

    # Rule prompt for instances that support int
    def rule_prompt_with_int_option(self, minimum, maximum):
        choice = questionary.select("Select rule", choices=['Enabled', 'Disabled', 'Int']).ask()
        if choice == 'Int':
            return questionary.text("Enter rule", validate=IntRange(minimum, maximum)).ask()
        else:
            return choice

    def select_sensor_targets(self):
        # Get list of all sensor IDs
        sensors = [key for key in self.config.keys() if is_sensor(key)]

        # Map strings displayed for each device option (syntax: "Nickname (type)") to their IDs
        targets_map = {}
        for key in [key for key in self.config.keys() if is_device(key)]:
            display = f"{self.config[key]['nickname']} ({self.config[key]['_type']})"
            targets_map[display] = key

        # Skip step if no devices
        if len(targets_map.keys()) == 0:
            return

        print("\nSelect target devices for each sensor")
        print("All targets will turn on when the sensor is activated")

        # Show checkbox prompt for each sensor with all devices as options
        for sensor in sensors:
            prompt = f"\nSelect targets for {self.config[sensor]['nickname']} ({self.config[sensor]['_type']})"
            targets = questionary.checkbox(prompt, choices=targets_map.keys()).ask()

            # Add selection to config
            self.config[sensor]['targets'] = [targets_map[i] for i in targets]

    def add_schedule_rule(self, config):
        timestamp = questionary.text("Enter timestamp (HH:MM)", validate=valid_timestamp).ask()
        rule = self.schedule_rule_prompt_router(config)
        return timestamp, rule

    def schedule_rules_prompt(self):
        for instance in [key for key in self.config if is_device_or_sensor(key)]:
            prompt = f"\nWould you like to add schedule rules for {self.config[instance]['nickname']}?"
            choice = questionary.select(prompt, choices=['Yes', 'No']).ask()
            if choice == 'Yes':
                while True:
                    timestamp, rule = self.add_schedule_rule(self.config[instance])
                    self.config[instance]['schedule'][timestamp] = rule
                    choice = questionary.select("\nAdd another?", choices=['Yes', 'No']).ask()
                    if choice == 'No':
                        break


if __name__ == '__main__':
    config = GenerateConfigFile()
    print(json.dumps(config.config, indent=4))
