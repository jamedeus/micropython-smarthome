#!/usr/bin/env python3

'''
Script used to generate micropython-smarthome config files on the command line.
Writes completed config to JSON file in config_dir (set in cli_config.json).

Call with no argument to generate a new config file (shows all prompts):
    ./config_generator.py

Call with path to an existing config file to edit (manually select prompts):
    ./config_generator.py ../config_files/living-room.json
'''

import os
import sys
import json
import questionary
from colorama import Fore
from instance_validators import validate_rules
from validate_config import validate_full_config
from validation_constants import (
    valid_device_pins,
    valid_sensor_pins,
    config_templates,
    ir_blaster_options
)
from helper_functions import (
    valid_ip,
    valid_uri,
    is_device,
    is_sensor,
    is_device_or_sensor,
    is_int
)
from config_prompt_validators import (
    IntRange,
    FloatRange,
    MinLength,
    NicknameValidator
)
from config_rule_prompts import (
    default_rule_prompt_router,
    schedule_rule_prompt_router,
    rule_limits_map,
    schedule_rule_timestamp_prompt,
    schedule_rule_timestamp_or_keyword_prompt
)
from cli_config_manager import CliConfigManager

# Read cli_config.json from disk (contains existing nodes and schedule keywords)
cli_config = CliConfigManager()


class GenerateConfigFile:
    '''Displays interactive menus used to create a full configuration file.
    Creates a new configuration file if instantiated with no argument.
    Edits an existing configuration file if config JSON passed as argument.
    Call run_prompt to show menu, call write_to_disk to save result as JSON
    file in config_dir (set in cli_config.json).
    '''

    def __init__(self, edit=None):
        if not edit:
            # Start with config skeleton
            self.config = {
                'metadata': {
                    'id': '',
                    'floor': '',
                    'location': '',
                    'schedule_keywords': cli_config.config['schedule_keywords']
                }
            }

            # Show default prompt when run_prompt called
            self.edit_mode = False

            # Set by __validate method
            self.passed_validation = False

        else:
            # Resolve path to existing config file, check for errors
            path = os.path.abspath(edit)
            if not path.endswith(".json"):
                print('Error: argument must be relative path to existing config.json')
                print('Example usage: ./CLI/config_generator.py /path/to/existing_config.json')
                raise SystemExit
            if not os.path.exists(path):
                print(f'Error: Config file "{edit}" not found')
                print('Example usage: ./CLI/config_generator.py /path/to/existing_config.json')
                raise SystemExit

            # Load existing config file
            with open(path, 'r', encoding='utf-8') as file:
                self.config = json.load(file)

            # Show edit prompt when run_prompt called
            self.edit_mode = True

        # List of device and sensor type options
        self.device_type_options = list(config_templates['device'].keys())
        self.sensor_type_options = list(config_templates['sensor'].keys())

        # List of category options
        self.category_options = ['Device', 'Sensor', 'IR Blaster', 'Done']

        # List of schedule keywords from config file
        self.schedule_keyword_options = list(cli_config.config['schedule_keywords'].keys())

    def run_prompt(self):
        '''Main entrypoint, displays a series of interactive menus used to
        generate a complete config file. Called when CLI script is run.

        Automatically walks through every prompt when creating new config,
        allows user to select next prompt when editing existing config.
        '''

        # Edit mode: print existing config and redirect to edit prompt
        if self.edit_mode:
            print("Editing existing config:\n")
            print(json.dumps(self.config, indent=4))
            self.run_edit_prompt()

        else:
            # Prompt user to enter metadata
            self.metadata_prompt()

            # Prompt user to add devices and sensors
            self.add_devices_and_sensors()

            # Prompt user to select targets for each sensor
            self.select_sensor_targets()

            # Validate finished config, print error if failed
            self.__validate()
            if self.passed_validation:
                # Show final prompt (allows user to continue editing)
                self.__finished_prompt()

    def run_edit_prompt(self):
        '''Displays interactive menu allowing the user to edit some or all
        sections of config.json, only displays prompts selected by user.

        Entrypoint when editing existing config file, called when user selects
        continue editing at the end of new config file prompt.
        '''

        # Prompt user to select action
        choice = None
        while choice != 'Done':
            choice = questionary.select(
                "\nWhat would you like to do?",
                choices=[
                    "Edit metadata",
                    "Add devices and sensors",
                    "Delete devices and sensors",
                    "Edit sensor targets",
                    "Done"
                ]
            ).unsafe_ask()
            if choice == 'Edit metadata':
                # Show metadata prompt with existing values pre-filled
                self.metadata_prompt(
                    self.config['metadata']['id'],
                    self.config['metadata']['floor'],
                    self.config['metadata']['location']
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

        # Validate finished config, print error if failed
        self.__validate()

    def __validate(self):
        '''Checks self.config for syntax errors by passing to validator, sets
        self.passed_validation attribute, prints error message if invalid.
        '''
        valid = validate_full_config(self.config)
        if valid is True:
            self.passed_validation = True
        else:
            print(f'{Fore.RED}ERROR: {valid}{Fore.RESET}')
            self.passed_validation = False

    def __finished_prompt(self):
        '''Shown when user completes final prompt.
        Prints completed config and gives user option to continue editing.
        '''
        print("\nFinished config:")
        print(json.dumps(self.config, indent=4))

        choice = questionary.select(
            "Continue editing?",
            choices=["Yes", "No"]
        ).unsafe_ask()
        if choice == "Yes":
            self.run_edit_prompt()

    def write_to_disk(self):
        '''Writes self.config to config_directory set in cli_config.json.'''
        config_path = cli_config.save_node_config_file(self.config)
        print(f"\nConfig saved as {os.path.split(config_path)[1]}")

    def metadata_prompt(self, name="", floor="", location=""):
        '''Prompts user for node name, location, and floor; adds to self.config.
        Optional arguments are used to set defaults when editing existing config.
        '''
        name = questionary.text(
            "Enter a descriptive name for this node:",
            validate=MinLength(1),
            default=name
        ).unsafe_ask()
        floor = questionary.text(
            "Enter floor number:",
            validate=is_int,
            default=floor
        ).unsafe_ask()
        location = questionary.text(
            "Enter a brief note about the node's physical location:",
            default=location
        ).unsafe_ask()

        self.config['metadata'].update({
            'id': name,
            'floor': int(floor),
            'location': location
        })

    def add_devices_and_sensors(self):
        '''Recursively prompts user to add devices, sensors, or IR Blaster
        until user "Done" option. Adds a section to self.config for each.
        '''
        choice = None
        while choice != 'Done':
            choice = questionary.select(
                "\nAdd instances?",
                choices=self.category_options
            ).unsafe_ask()
            if choice == 'Device':
                # Get next device index
                index = len([i for i in self.config if is_device(i)]) + 1
                # Run prompts, write user selection to new self.config section
                self.config[f'device{index}'] = self.__configure_device()
            elif choice == 'Sensor':
                # Get next sensor index
                index = len([i for i in self.config if is_sensor(i)]) + 1
                # Run prompts, write user selection to new self.config section
                self.config[f'sensor{index}'] = self.__configure_sensor()
            elif choice == 'IR Blaster':
                self.configure_ir_blaster()

    def delete_devices_and_sensors(self):
        '''Displays checkbox for each existing device and sensor, removes user
        selection from self.config.
        '''

        # Map display string for each existing device and sensor to their IDs
        # Syntax: {"Nickname (type)": "device1"}
        instances_map = {f"{params['nickname']} ({params['_type']})": instance
                         for instance, params in self.config.items()
                         if is_device_or_sensor(instance)}

        # Skip prompt if no devices or sensors configured
        if len(instances_map) == 0:
            return

        # Prompt user to select all devices and sensors they wish to delete
        delete = questionary.checkbox(
            "Select devices and sensors to delete",
            choices=instances_map.keys()
        ).unsafe_ask()

        # Delete instances from config file
        for i in delete:
            del self.config[instances_map[i]]

        # Prevent gaps in index (eg: [device1, device3] => [device1, device2]
        self.__reindex_devices_and_sensors()

    def __reindex_devices_and_sensors(self):
        '''Called after deleting devices/sensors to ensure sequential index.'''

        # Back up devices and sensors
        devices = [self.config[i] for i in self.config if is_device(i)]
        sensors = [self.config[i] for i in self.config if is_sensor(i)]

        # Delete all devices and sensors
        self.config = {key: value for key, value in self.config.items()
                       if not is_device_or_sensor(key)}

        # Add devices and sensors back with sequential indices
        for index, instance in enumerate(devices, 1):
            self.config[f'device{index}'] = instance
        for index, instance in enumerate(sensors, 1):
            self.config[f'sensor{index}'] = instance

    def __device_type(self):
        '''Prompts user to select from a list of valid device types.
        First prompt shown by __configure_device, used to get config template.
        '''
        return questionary.select(
            "Select device type",
            choices=self.device_type_options
        ).unsafe_ask()

    def __sensor_type(self):
        '''Prompts user to select from a list of valid sensor types.
        First prompt shown by __configure_sensor, used to get config template.
        '''

        # Get list of existing sensor types
        sensor_types = [self.config[sensor]["_type"]
                        for sensor in self.config if is_sensor(sensor)]

        # Remove si7021 option if already configured (multiple not supported)
        if "si7021" in sensor_types:
            options = [_type for _type in self.sensor_type_options
                       if not _type.startswith("SI7021")]
        else:
            options = self.sensor_type_options

        return questionary.select(
            "Select sensor type",
            choices=options
        ).unsafe_ask()

    def __nickname_prompt(self):
        '''Prompts user to enter a device/sensor nickname, returns user input.
        Does not accept duplicate nicknames that already exist in self.config.
        '''

        # Get list of existing nicknames for validators (prevent duplicates)
        used_nicknames = [self.config[i]['nickname'] for i in self.config
                          if 'nickname' in self.config[i].keys()]
        return questionary.text(
            "Enter a memorable nickname:",
            validate=NicknameValidator(used_nicknames)
        ).unsafe_ask()

    def __pin_prompt(self, valid_pins, prompt="Select pin"):
        '''Prompts user to select from a list of unused pins, returns selection.
        Takes a list of pin options as argument, removes pins that already
        exist in self.config to prevent user selecting duplicate pin.
        '''

        # Get list of pins used by existing devices and sensors
        used_pins = [self.config[i]['pin'] for i in self.config
                     if 'pin' in self.config[i].keys()]
        # Get list of available pins, run prompt
        choices = [pin for pin in valid_pins if pin not in used_pins]
        return questionary.select(prompt, choices=choices).unsafe_ask()

    def __ip_address_prompt(self):
        '''Prompts user to enter an IPv4 address, returns user input.
        Enforces syntax, will not accept an invalid IP.
        '''
        return questionary.text(
            "Enter IP address:",
            validate=valid_ip
        ).unsafe_ask()

    def __apitarget_ip_prompt(self):
        '''Prompts user to select from a list of friendly names of all nodes in
        cli_config.json, returns IP address of selected node.
        '''

        # Show prompt with names of all existing nodes
        target = questionary.select(
            "Select target node",
            choices=list(cli_config.config['nodes'].keys())
        ).unsafe_ask()
        return cli_config.config['nodes'][target]

    def __configure_device(self, config=None):
        '''Prompts user to select device type followed by all required params
        for the chosen device. Validates user selection before returning - if
        fails the invalid params are reset and their prompts are shown again.
        Returns completed config section with all selected params once valid.
        '''

        # Prompt user for device type, get config skeleton
        if config is None:
            config = config_templates['device'][self.__device_type()].copy()
            _type = config['_type']
        # Previously failed validation, repeat prompts for invalid params
        else:
            _type = config['_type']

        # Prompt user for all parameters with missing value
        for i in [i for i in config if config[i] == "placeholder"]:
            if i == "nickname":
                config[i] = self.__nickname_prompt()

            elif i == "pin":
                config[i] = self.__pin_prompt(valid_device_pins)

            elif i.startswith("pin_"):
                config[i] = self.__pin_prompt(
                    valid_device_pins,
                    f"Select {i.split('_')[1]} pin"
                )

            elif i == "default_rule":
                config[i] = default_rule_prompt_router(config)

            elif i == "min_rule":
                config[i] = questionary.text(
                    "Enter minimum rule:",
                    default=str(rule_limits_map[_type][0]),
                    validate=IntRange(*rule_limits_map[_type])
                ).unsafe_ask()

            elif i == "max_rule":
                config[i] = questionary.text(
                    "Enter maximum rule:",
                    default=str(rule_limits_map[_type][1]),
                    validate=IntRange(config['min_rule'], rule_limits_map[_type][1])
                ).unsafe_ask()

            elif i == "uri":
                config[i] = questionary.text(
                    "Enter base URI (no endpoint path):",
                    validate=valid_uri
                ).unsafe_ask()

            elif i.endswith("_path"):
                action = i.split("_")[0]
                config[i] = questionary.text(
                    f"Enter endpoint for {action.upper()} action"
                ).unsafe_ask()

            # ApiTarget has own IP prompt (select friendly name from nodes in cli_config.json)
            elif i == "ip" and _type == "api-target":
                config[i] = self.__apitarget_ip_prompt()

            elif i == "ip":
                config[i] = self.__ip_address_prompt()

        # Prompt user to add schedule rules
        config = self.__schedule_rule_prompt(config)

        # Confirm all selections are valid
        valid = validate_rules(config)
        if valid is not True:
            # Print error, remove potentially invalid parameters and re-prompt
            print(f'{Fore.RED}ERROR{Fore.RESET}: {valid}')
            print('Resetting relevant options, please try again')
            return self.__configure_device(self.__reset_config_template(config))
        return config

    def __configure_sensor(self, config=None):
        '''Prompts user to select sensor type followed by all required params
        for the chosen sensor. Validates user selection before returning - if
        fails the invalid params are reset and their prompts are shown again.
        Returns completed config section with all selected params once valid.
        '''

        # Prompt user for sensor type, get config skeleton
        if config is None:
            config = config_templates['sensor'][self.__sensor_type()].copy()

        # Prompt user for all parameters with missing value
        for i in [i for i in config if config[i] == "placeholder"]:
            if i == "nickname":
                config[i] = self.__nickname_prompt()

            elif i == "pin":
                config[i] = self.__pin_prompt(valid_sensor_pins)

            elif i.startswith("pin_"):
                config[i] = self.__pin_prompt(
                    valid_sensor_pins,
                    f"Select {i.split('_')[1]} pin"
                )

            elif i == "default_rule":
                config[i] = default_rule_prompt_router(config)

            elif i == "ip":
                config[i] = self.__ip_address_prompt()

            elif i == "mode":
                config[i] = questionary.select(
                    "Select mode",
                    choices=['cool', 'heat']
                ).unsafe_ask()

            elif i == "units":
                config[i] = questionary.select(
                    "Select units",
                    choices=['fahrenheit', 'celsius', 'kelvin']
                ).unsafe_ask()

            elif i == "tolerance":
                config[i] = questionary.text(
                    "Enter temperature tolerance:",
                    validate=FloatRange(0, 10)
                ).unsafe_ask()

        # Prompt user to add schedule rules
        config = self.__schedule_rule_prompt(config)

        # Confirm all selections are valid
        valid = validate_rules(config)
        if valid is not True:
            # Print error, remove potentially invalid parameters and re-prompt
            print(f'{Fore.RED}ERROR{Fore.RESET}: {valid}')
            print('Resetting relevant options, please try again')
            return self.__configure_sensor(self.__reset_config_template(config))
        return config

    def configure_ir_blaster(self):
        '''Prompts user to select IR Blaster pin and target(s), adds completed
        section to self.config.
        '''

        # Prompt user for pin and targets
        pin = self.__pin_prompt(valid_device_pins)
        targets = questionary.checkbox(
            "Select target devices",
            choices=list(ir_blaster_options.keys())
        ).unsafe_ask()

        # Add to config
        self.config['ir_blaster'] = {
            "pin": pin,
            "target": targets
        }

        # Remove option from menun (multiple ir blasters not supported)
        self.category_options.remove('IR Blaster')

    def __reset_config_template(self, config):
        '''Takes config section that failed validation, replaces potentially
        invalid params with placeholders. Used by __configure_device and
        __configure_sensor to re-prompt user without repeating all questions.
        '''
        for i in config:
            if i not in ['nickname', 'pin', '_type', 'schedule', 'targets']:
                config[i] = 'placeholder'
            if i == 'schedule':
                config[i] = {}
        return config

    def select_sensor_targets(self):
        '''Prompts user to select targets for each configured sensor.
        Displays checkbox list with all configured devices for each sensor.
        Adds user selection to sensor targets param in self.config.
        '''

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
                options.append(questionary.Choice(
                    display,
                    checked=bool(device in self.config[sensor]['targets'])
                ))

            nickname = self.config[sensor]['nickname']
            _type = self.config[sensor]['_type']
            prompt = f"\nSelect targets for {nickname} ({_type})"
            targets = questionary.checkbox(prompt, choices=options).unsafe_ask()

            # Add selection to config
            self.config[sensor]['targets'] = [targets_map[i] for i in targets]

    def __schedule_rule_prompt(self, config):
        '''Takes device or sensor section argument, recursively prompts user to
        add schedule rules until "Done" selected. Returns argument with added
        schedule rules. Called by __configure_device and __configure_sensor.
        '''

        prompt = f"\nWould you like to add schedule rules for {config['nickname']}?"
        if questionary.select(prompt, choices=['Yes', 'No']).unsafe_ask() == 'Yes':
            while True:
                config = self.__add_schedule_rule(config)
                choice = questionary.select(
                    "\nAdd another?",
                    choices=['Yes', 'No']
                ).unsafe_ask()
                if choice == 'No':
                    break
        return config

    def __add_schedule_rule(self, config):
        '''Takes device or sensor section argument, prompts user to select a
        single schedule rule timestamp and rule, returns updated section.
        Called on each iteration of __schedule_rule_prompt loop.
        '''

        # Prompt user to select timestamp or keyword if keywords are configured
        if self.schedule_keyword_options:
            timestamp = schedule_rule_timestamp_or_keyword_prompt(
                self.schedule_keyword_options
            )
        # Prompt for timestamp if no keywords are available
        else:
            timestamp = schedule_rule_timestamp_prompt()
        rule = schedule_rule_prompt_router(config)
        config['schedule'][timestamp] = rule
        return config


def main():
    '''Command line entrypoint, handles args and shows prompt'''

    if len(sys.argv) > 1:
        # Instantiate in edit mode with path to existing config
        generator = GenerateConfigFile(sys.argv[1])
    else:
        generator = GenerateConfigFile()

    try:
        generator.run_prompt()
    except KeyboardInterrupt as interrupt:  # pragma: no cover
        raise SystemExit from interrupt

    # Write to disk if passed validation
    if generator.passed_validation:
        generator.write_to_disk()


if __name__ == '__main__':  # pragma: no cover
    main()
