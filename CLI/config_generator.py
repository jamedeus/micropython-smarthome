#!/usr/bin/python3

import os
import sys
import json
import questionary
from colorama import Fore
from instance_validators import validate_rules
from validate_config import validate_full_config
from validation_constants import valid_device_pins, valid_sensor_pins, config_templates
from config_prompt_validators import IntRange, FloatRange, MinLength, NicknameValidator
from config_rule_prompts import default_rule_prompt_router, schedule_rule_prompt_router, rule_limits_map
from helper_functions import (
    valid_ip,
    valid_timestamp,
    is_device,
    is_sensor,
    is_device_or_sensor,
    is_int,
    get_schedule_keywords_dict,
    get_existing_nodes,
    get_cli_config
)


class GenerateConfigFile:
    def __init__(self, edit=None):
        if not edit:
            # Start with config skeleton
            self.config = {
                'metadata': {
                    'id': '',
                    'floor': '',
                    'location': '',
                    'schedule_keywords': get_schedule_keywords_dict()
                },
                'wifi': {
                    'ssid': '',
                    'password': ''
                }
            }

            # Lists for already-used pins and nicknames (prevent duplicates)
            self.used_pins = []
            self.used_nicknames = []

            # Show default prompt when run_prompt called
            self.edit_mode = False

        else:
            # Resolve path to existing config file, check for errors
            path = os.path.abspath(edit)
            if not path.endswith(".json"):
                print('Error: argument must be relative path to existing config.json')
                print('Example usage: ./CLI/config_generator.py /path/to/existing_config.json')
                raise SystemExit
            elif not os.path.exists(path):
                print(f'Error: Config file "{sys.argv[1]}" not found')
                print('Example usage: ./CLI/config_generator.py /path/to/existing_config.json')
                raise SystemExit

            # Load existing config file
            with open(path, 'r') as file:
                self.config = json.load(file)

            # Parse already-used pins and nicknames (prevent duplicates)
            self.used_pins = [self.config[i]['pin'] for i in self.config if 'pin' in self.config[i].keys()]
            self.used_nicknames = [
                self.config[i]['nickname'] for i in self.config if 'nickname' in self.config[i].keys()
            ]

            # Show edit prompt when run_prompt called
            self.edit_mode = True

        # List of device and sensor type options
        self.device_type_options = list(config_templates['device'].keys())
        self.sensor_type_options = list(config_templates['sensor'].keys())

        # List of category options
        self.category_options = ['Device', 'Sensor', 'IR Blaster', 'Done']

        # List of schedule keywords from config file
        self.schedule_keyword_options = list(get_schedule_keywords_dict().keys())

        # Dict of existing nodes, used to populate ApiTarget options
        self.existing_nodes = get_existing_nodes()

    def run_prompt(self):
        # Edit mode: print existing config and redirect to edit prompt
        if self.edit_mode:
            print("Editing existing config:\n")
            print(json.dumps(self.config, indent=4))
            return self.run_edit_prompt()

        # Prompt user to enter metadata and wifi credentials
        self.metadata_prompt()
        self.wifi_prompt()

        # Prompt user to add devices and sensors
        self.add_devices_and_sensors()

        # Prompt user to select targets for each sensor
        self.select_sensor_targets()

        # Validate finished config, print error if failed
        self.validate()
        if self.passed_validation:
            # Show final prompt (allows user to continue editing)
            self.finished_prompt()

    def run_edit_prompt(self):
        # Prompt user to select action
        while True:
            choice = questionary.select(
                "\nWhat would you like to do?",
                choices=[
                    "Edit metadata",
                    "Edit wifi credentials",
                    "Add devices and sensors",
                    "Delete devices and sensors",
                    "Edit sensor targets",
                    "Done"
                ]
            ).ask()
            if choice == 'Edit metadata':
                # Show metadata prompt with existing values pre-filled
                self.metadata_prompt(
                    self.config['metadata']['id'],
                    self.config['metadata']['floor'],
                    self.config['metadata']['location']
                )
            elif choice == 'Edit wifi credentials':
                # Show wifi prompt with existing values pre-filled
                self.wifi_prompt(
                    self.config['wifi']['ssid'],
                    self.config['wifi']['password']
                )
            elif choice == 'Add devices and sensors':
                # Prompt user to add devices and sensors
                self.add_devices_and_sensors()
                # Prompt user to delete existing devices and sensors
            elif choice == 'Delete devices and sensors':
                self.delete_devices_and_sensors()
            elif choice == 'Edit sensor targets':
                # Prompt user to select targets for each sensor
                self.select_sensor_targets()
            elif choice == 'Done':
                break

        # Validate finished config, print error if failed
        self.validate()

    # Passes config object to validator, sets passed_validation attribute,
    # prints error message if validation failed
    def validate(self):
        valid = validate_full_config(self.config)
        if valid is True:
            self.passed_validation = True
        else:
            print(f'{Fore.RED}ERROR: {valid}{Fore.RESET}')
            self.passed_validation = False

    # Shown when finished creating new config
    # Prints completed config and gives user option to continue editing
    def finished_prompt(self):
        print("\nFinished config:")
        print(json.dumps(self.config, indent=4))

        choice = questionary.select("Continue editing?", choices=["Yes", "No"]).ask()
        if choice == "Yes":
            self.run_edit_prompt()

    def write_to_disk(self):
        # Get filename (all lowercase, replace spaces with hyphens)
        filename = self.config["metadata"]["id"].lower().replace(" ", "-") + ".json"

        # Write to config_directory (set in cli_config.json)
        with open(os.path.join(get_cli_config()['config_directory'], filename), 'w') as file:
            json.dump(self.config, file)

        print(f"\nConfig saved as {filename}")

    # Prompt user for node name and location metadata, add to self.config
    # Optional arguments are used to set defaults when editing existing config
    def metadata_prompt(self, name="", floor="", location=""):
        name = questionary.text("Enter a descriptive name for this node:", validate=MinLength(1), default=name).ask()
        floor = questionary.text("Enter floor number:", validate=is_int, default=floor).ask()
        location = questionary.text("Enter a brief note about the node's physical location:", default=location).ask()

        self.config['metadata'].update({'id': name, 'floor': floor, 'location': location})

    # Prompt user for wifi credentials, add to self.config
    # Optional arguments are used to set defaults when editing existing config
    def wifi_prompt(self, ssid="", password=""):
        ssid = questionary.text("Enter wifi SSID (2.4 GHz only):", validate=MinLength(1), default=ssid).ask()
        password = questionary.password("Enter wifi password:", validate=MinLength(8), default=password).ask()

        self.config['wifi'].update({'ssid': ssid, 'password': password})

    def add_devices_and_sensors(self):
        # Lists to store + count device and sensor sections
        devices = [self.config[i] for i in self.config if is_device(i)]
        sensors = [self.config[i] for i in self.config if is_sensor(i)]

        # Prompt user to configure devices and sensors
        # Output of each device/sensor prompt is added to lists above
        while True:
            choice = questionary.select("\nAdd instances?", choices=self.category_options).ask()
            if choice == 'Device':
                devices.append(self.configure_device())
            elif choice == 'Sensor':
                sensors.append(self.configure_sensor())
            elif choice == 'IR Blaster':
                self.configure_ir_blaster()
            elif choice == 'Done':
                break

        # Add sequential device and sensor keys (device1, device2, etc)
        # for each item in devices and sensors
        for index, instance in enumerate(devices, 1):
            self.config[f'device{index}'] = instance
        for index, instance in enumerate(sensors, 1):
            self.config[f'sensor{index}'] = instance

    def delete_devices_and_sensors(self):
        # Get list of all sensor and device IDs
        instances = [key for key in self.config.keys() if is_device_or_sensor(key)]

        # Skip step if no instances
        if len(instances) == 0:
            return

        # Map strings displayed for each option (syntax: "Nickname (type)") to their IDs
        instances_map = {}
        for key in instances:
            display = f"{self.config[key]['nickname']} ({self.config[key]['_type']})"
            instances_map[display] = key

        # Prompt user to select all devices and sensors they wish to delete
        delete = questionary.checkbox("Select devices and sensors to delete", choices=instances_map.keys()).ask()

        # Delete instances from config file, remove pin/nickname from used lists
        for i in delete:
            self.used_nicknames.remove(self.config[instances_map[i]]['nickname'])
            if 'pin' in self.config[instances_map[i]].keys():
                self.used_pins.remove(self.config[instances_map[i]]['pin'])
            del self.config[instances_map[i]]

    # Prompt user to select from a list of valid device types
    # Used to get template in configure_device
    def device_type(self):
        return questionary.select(
            "Select device type",
            choices=self.device_type_options
        ).ask()

    # Prompt user to select from a list of valid sensor types
    # Used to get template in configure_sensor
    def sensor_type(self):
        return questionary.select(
            "Select sensor type",
            choices=self.sensor_type_options
        ).ask()

    # Prompt user for a nickname, add to used_nicknames list, return
    def nickname_prompt(self):
        nickname = questionary.text(
            "Enter a memorable nickname:",
            validate=NicknameValidator(self.used_nicknames)
        ).ask()
        self.used_nicknames.append(nickname)
        return nickname

    # Prompt user to select pin, add to used_pins list, return
    # Takes list of options as arg, removes already-used pins to prevent duplicates
    def pin_prompt(self, valid_pins, prompt="Select pin"):
        choices = [pin for pin in valid_pins if pin not in self.used_pins]
        pin = questionary.select(prompt, choices=choices).ask()
        self.used_pins.append(pin)
        return pin

    # Prompt user to enter an IP address, enforces syntax
    def ip_address_prompt(self):
        return questionary.text("Enter IP address:", validate=valid_ip).ask()

    # Prompt user to select from existing node friendly names
    # Returns IP of selected node
    def apitarget_ip_prompt(self):
        options = list(self.existing_nodes.keys())
        target = questionary.select("Select target node", choices=options).ask()
        return self.existing_nodes[target]['ip']

    # Prompt user to select device type and all required params.
    # Validates config before returning - if validation fails, some
    # params are removed and the function is called with partial config
    # as config arg (re-prompts user without repeating all questions).
    def configure_device(self, config=None):
        # Prompt user for device type, get config skeleton
        if config is None:
            config = config_templates['device'][self.device_type()].copy()
            _type = config['_type']
        # Previously failed validation, repeat prompts for invalid params
        else:
            _type = config['_type']

        # Prompt user for all parameters with missing value
        for i in [i for i in config if config[i] == "placeholder"]:
            if i == "nickname":
                config[i] = self.nickname_prompt()

            elif i == "pin":
                config[i] = self.pin_prompt(valid_device_pins)

            elif i.startswith("pin_"):
                config[i] = self.pin_prompt(valid_device_pins, f"Select {i.split('_')[1]} pin")

            elif i == "default_rule":
                config[i] = default_rule_prompt_router(config)

            elif i == "min_bright":
                config[i] = questionary.text(
                    "Enter minimum brightness:",
                    default=str(rule_limits_map[_type][0]),
                    validate=IntRange(*rule_limits_map[_type])
                ).ask()

            elif i == "max_bright":
                config[i] = questionary.text(
                    "Enter maximum brightness:",
                    default=str(rule_limits_map[_type][1]),
                    validate=IntRange(config['min_bright'], rule_limits_map[_type][1])
                ).ask()

            # ApiTarget has own IP prompt (select friendly name from nodes in cli_config.json)
            elif i == "ip" and _type == "api-target":
                config[i] = self.apitarget_ip_prompt()

            elif i == "ip":
                config[i] = self.ip_address_prompt()

        # Prompt user to add schedule rules
        config = self.schedule_rule_prompt(config)

        # Confirm all selections are valid
        valid = validate_rules(config)
        if valid is not True:
            # Print error, remove potentially invalid parameters and re-prompt
            print(f'{Fore.RED}ERROR{Fore.RESET}: {valid}')
            print('Resetting relevant options, please try again')
            return self.configure_device(self.reset_config_template(config))
        else:
            return config

    # Prompt user to select sensor type and all required params.
    # Validates config before returning - if validation fails, some
    # params are removed and the function is called with partial config
    # as config arg (re-prompts user without repeating all questions).
    def configure_sensor(self, config=None):
        # Prompt user for sensor type, get config skeleton
        if config is None:
            config = config_templates['sensor'][self.sensor_type()].copy()

        # Prompt user for all parameters with missing value
        for i in [i for i in config if config[i] == "placeholder"]:
            if i == "nickname":
                config[i] = self.nickname_prompt()

            elif i == "pin":
                config[i] = self.pin_prompt(valid_sensor_pins)

            elif i.startswith("pin_"):
                config[i] = self.pin_prompt(valid_sensor_pins, f"Select {i.split('_')[1]} pin")

            elif i == "default_rule":
                config[i] = default_rule_prompt_router(config)

            elif i == "ip":
                config[i] = self.ip_address_prompt()

            elif i == "mode":
                config[i] = questionary.select("Select mode", choices=['cool', 'heat']).ask()

            elif i == "tolerance":
                config[i] = questionary.text("Enter temperature tolerance:", validate=FloatRange(0, 10)).ask()

        # Prompt user to add schedule rules
        config = self.schedule_rule_prompt(config)

        # Confirm all selections are valid
        valid = validate_rules(config)
        if valid is not True:
            # Print error, remove potentially invalid parameters and re-prompt
            print(f'{Fore.RED}ERROR{Fore.RESET}: {valid}')
            print('Resetting relevant options, please try again')
            return self.configure_sensor(self.reset_config_template(config))
        else:
            # If Thermostat added remove option from menu (cannot have multiple)
            if config['_type'] == 'si7021':
                self.sensor_type_options.remove('Thermostat')
            return config

    def configure_ir_blaster(self):
        # Prompt user for pin and targets
        pin = self.pin_prompt(valid_device_pins)
        targets = questionary.checkbox("Select target devices", choices=['tv', 'ac']).ask()

        # Add to config
        self.config['ir_blaster'] = {
            "pin": pin,
            "target": targets
        }

        # Remove option from menun (multiple ir blasters not supported)
        self.category_options.remove('IR Blaster')

    # Takes config that failed validation, replaces potentially invalid params
    # with placeholder. Used to re-prompt user without repeating all questions.
    def reset_config_template(self, config):
        for i in config:
            if i not in ['nickname', 'pin', '_type', 'schedule', 'targets']:
                config[i] = 'placeholder'
            if i == 'schedule':
                config[i] = {}
        return config

    # Iterate all configured sensors, display checkbox prompt for each
    # with all configured devices as options. Add all checked devices
    # to sensor targets list.
    def select_sensor_targets(self):
        # Get lists of all sensor and device IDs
        sensors = [key for key in self.config.keys() if is_sensor(key)]
        devices = [key for key in self.config.keys() if is_device(key)]

        # Skip step if no devices
        if len(devices) == 0:
            return

        # Map strings displayed for each device option (syntax: "Nickname (type)") to their IDs
        targets_map = {}
        for key in devices:
            display = f"{self.config[key]['nickname']} ({self.config[key]['_type']})"
            targets_map[display] = key

        print("\nSelect target devices for each sensor")
        print("All targets will turn on when the sensor is activated")

        # Show checkbox prompt for each sensor with all devices as options
        for sensor in sensors:
            # Build Choice objects for each device option
            # Pre-select option if device is already a target in existing config file
            options = []
            for display, device in targets_map.items():
                options.append(questionary.Choice(display, checked=bool(device in self.config[sensor]['targets'])))

            prompt = f"\nSelect targets for {self.config[sensor]['nickname']} ({self.config[sensor]['_type']})"
            targets = questionary.checkbox(prompt, choices=options).ask()

            # Add selection to config
            self.config[sensor]['targets'] = [targets_map[i] for i in targets]

    # Takes instance config, prompts to add schedule rules in loop until
    # user selects done. Returns config with all selected schedule rules.
    def schedule_rule_prompt(self, config):
        prompt = f"\nWould you like to add schedule rules for {config['nickname']}?"
        if questionary.select(prompt, choices=['Yes', 'No']).ask() == 'Yes':
            while True:
                config = self.add_schedule_rule(config)
                choice = questionary.select("\nAdd another?", choices=['Yes', 'No']).ask()
                if choice == 'No':
                    break
        return config

    # Takes config, prompts user to add a single schedule rule, returns
    # config with rule added. Called by loop in schedule_rule_prompt.
    def add_schedule_rule(self, config):
        # Prompt user to select timestamp or keyword if keywords are configured
        if len(self.schedule_keyword_options):
            timestamp = self.schedule_rule_timestamp_or_keyword_prompt()
        # Prompt for timestamp if no keywords are available
        else:
            timestamp = self.schedule_rule_timestamp_prompt()
        rule = schedule_rule_prompt_router(config)
        config['schedule'][timestamp] = rule
        return config

    def schedule_rule_timestamp_prompt(self):
        return questionary.text("Enter timestamp (HH:MM):", validate=valid_timestamp).ask()

    def schedule_rule_timestamp_or_keyword_prompt(self):
        choice = questionary.select("\nTimestamp or keyword?", choices=['Timestamp', 'Keyword']).ask()
        if choice == 'Timestamp':
            return self.schedule_rule_timestamp_prompt()
        else:
            return questionary.select("\nSelect keyword", choices=self.schedule_keyword_options).ask()


if __name__ == '__main__':
    if len(sys.argv) > 1:
        # Instantiate in edit mode with path to existing config
        config = GenerateConfigFile(sys.argv[1])
    else:
        config = GenerateConfigFile()

    config.run_prompt()

    # Write to disk if passed validation
    if config.passed_validation:
        config.write_to_disk()
