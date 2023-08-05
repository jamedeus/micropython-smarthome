#!/usr/bin/python3

import os
import json
import questionary
from questionary import Validator, ValidationError
from colorama import Fore
from instance_validators import validate_rules
from validation_constants import (
    valid_device_pins,
    valid_sensor_pins,
    config_templates,
    ir_blaster_options,
    device_endpoints,
    sensor_endpoints
)
from helper_functions import (
    valid_ip,
    valid_timestamp,
    is_device,
    is_sensor,
    is_device_or_sensor,
    is_int,
    is_float,
    get_schedule_keywords_dict,
    get_existing_nodes,
    get_cli_config
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


class MinLength(Validator):
    def __init__(self, min_length):
        self.min_length = int(min_length)

    def validate(self, document):
        if len(str(document.text)) >= self.min_length:
            return True
        else:
            raise ValidationError(message=f"Enter {self.min_length} or more characters")


# Instantiated with list of already-used nicknames
class NicknameValidator(Validator):
    def __init__(self, used_nicknames):
        self.used_nicknames = used_nicknames

    def validate(self, document):
        if len(document.text) == 0:
            raise ValidationError(message="Nickname cannot be blank")
        elif document.text in self.used_nicknames:
            raise ValidationError(message=f'Nickname "{document.text}" already used')
        else:
            return True


class GenerateConfigFile:
    def __init__(self):
        # Config skeleton
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

        # Lists of already-used pins and nicknames (prevent duplicates)
        self.used_pins = []
        self.used_nicknames = []

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
        # Prompt user to enter metadata and wifi credentials
        self.metadata_prompt()
        self.wifi_prompt()

        # Prompt user to add devices and sensors
        self.add_devices_and_sensors()

        # Prompt user to select targets for each sensor
        self.select_sensor_targets()

    def write_to_disk(self):
        # Get filename (all lowercase, replace spaces with hyphens)
        filename = self.config["metadata"]["id"].lower().replace(" ", "-") + ".json"

        # Write to config_directory (set in cli_config.json)
        with open(os.path.join(get_cli_config()['config_directory'], filename), 'w') as file:
            json.dump(self.config, file)

    # Prompt user for node name and location metadata, add to self.config
    def metadata_prompt(self):
        name = questionary.text("Enter a descriptive name for this node", validate=MinLength(1)).ask()
        floor = questionary.text("Enter floor number", validate=is_int).ask()
        location = questionary.text("Enter a brief description of the node's physical location").ask()

        self.config['metadata'].update({'id': name, 'floor': floor, 'location': location})

    # Prompt user for wifi credentials, add to self.config
    def wifi_prompt(self):
        ssid = questionary.text("Enter wifi SSID (2.4 GHz only)", validate=MinLength(1)).ask()
        password = questionary.password("Enter wifi password", validate=MinLength(8)).ask()

        self.config['wifi'].update({'ssid': ssid, 'password': password})

    def add_devices_and_sensors(self):
        # Lists to store + count device and sensor sections
        devices = []
        sensors = []

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
            "Enter a memorable nickname",
            validate=NicknameValidator(self.used_nicknames)
        ).ask()
        self.used_nicknames.append(nickname)
        return nickname

    # Prompt user to select pin, add to used_pins list, return
    # Takes list of options as arg, removes already-used pins to prevent duplicates
    def pin_prompt(self, valid_pins):
        choices = [pin for pin in valid_pins if pin not in self.used_pins]
        pin = questionary.select("Select pin", choices=choices).ask()
        self.used_pins.append(pin)
        return pin

    # Prompt user to enter an IP address, enforces syntax
    def ip_address_prompt(self):
        return questionary.text("Enter IP address", validate=valid_ip).ask()

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

            elif i == "default_rule":
                config[i] = self.default_rule_prompt_router(config)

            elif i == "ip":
                config[i] = self.ip_address_prompt()

            elif i == "mode":
                config[i] = questionary.select("Select mode", choices=['cool', 'heat']).ask()

            elif i == "tolerance":
                config[i] = questionary.text("Enter temperature tolerance", validate=FloatRange(0, 10)).ask()

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

    # Takes partial config, runs appropriate default_rule prompt
    # based on instance type, returns user selection
    def default_rule_prompt_router(self, config):
        _type = config['_type']
        # DimmableLight subclasses require int default_rule
        if _type in ['dimmer', 'bulb', 'pwm', 'wled']:
            return questionary.text(
                "Enter default rule",
                validate=IntRange(config['min_bright'], config['max_bright'])
            ).ask()
        # Certain sensors require int default_rule
        elif _type in ['pir', 'si7021']:
            return questionary.text("Enter default rule", validate=FloatRange(*rule_limits[_type])).ask()
        # Dummy does not support enabled/disabled for default_rule, must be on or off
        elif _type == 'dummy':
            return questionary.select("Enter default rule", choices=['On', 'Off']).ask()
        # ApiTarget has own prompt due to complexity
        elif _type == 'api-target':
            return self.api_target_rule_prompt(config)
        # All other instance types only support Enabled and Disabled
        else:
            return questionary.select("Enter default rule", choices=['Enabled', 'Disabled']).ask()

    # Takes partial config, runs appropriate schedule rule prompt
    # based on instance type, returns user selection
    def schedule_rule_prompt_router(self, config):
        _type = config['_type']
        # DimmableLight subclasses support int and fade rules in addition to enabled/disabled
        if _type in ['dimmer', 'bulb', 'pwm', 'wled']:
            return self.rule_prompt_int_and_fade_options(config['min_bright'], config['max_bright'])
        # Some sensors support int in addition to enabled/disabled
        elif _type in ['pir', 'si7021']:
            return self.rule_prompt_with_float_option(*rule_limits[_type])
        # Summy supports On and Off in addition to enabled/disabled
        elif _type == 'dummy':
            return questionary.select("Enter default rule", choices=['Enabled', 'Disabled', 'On', 'Off']).ask()
        # ApiTarget has own prompt due to complexity
        elif _type == 'api-target':
            return self.rule_prompt_with_api_call_prompt(config)
        # All other instance types only support Enabled and Disabled
        else:
            return questionary.select("Enter default rule", choices=['Enabled', 'Disabled']).ask()

    # Rule prompt for instances that support float in addition to enabled/disabled
    def rule_prompt_with_float_option(self, minimum, maximum):
        choice = questionary.select("Select rule", choices=['Enabled', 'Disabled', 'Float']).ask()
        if choice == 'Float':
            return questionary.text("Enter rule", validate=FloatRange(minimum, maximum)).ask()
        else:
            return choice

    # Rule prompt for DimmableLight instances, includes int and fade in addition to enabled/disabled
    def rule_prompt_int_and_fade_options(self, minimum, maximum):
        choice = questionary.select("Select rule", choices=['Enabled', 'Disabled', 'Int', 'Fade']).ask()
        if choice == 'Int':
            return questionary.text("Enter rule", validate=IntRange(minimum, maximum)).ask()
        if choice == 'Fade':
            target = questionary.text("Enter target brightness", validate=IntRange(minimum, maximum)).ask()
            period = questionary.text("Enter duration in seconds", validate=IntRange(1, 86400)).ask()
            return f'fade/{target}/{period}'
        else:
            return choice

    # Schedule rule prompt for ApiTarget, includes API call option in addition to enabled/disabled
    # Only used for schedule rules, enabled/disabled are invalid as default_rule
    def rule_prompt_with_api_call_prompt(self, config):
        choice = questionary.select("Select rule", choices=['Enabled', 'Disabled', 'API Call']).ask()
        if choice == 'API Call':
            return self.api_target_rule_prompt(config)
        else:
            return choice

    # Prompt user to select API call parameters for both ON and OFF actions
    # Returns complete ApiTarget rule dict
    def api_target_rule_prompt(self, config):
        if questionary.confirm("Should an API call be made when the device is turned ON?").ask():
            print('\nAPI Target ON action')
            on_action = self.api_call_prompt(config)
            print()
        else:
            on_action = ['ignore']

        if questionary.confirm("Should an API call be made when the device is turned OFF?").ask():
            print('\nAPI Target OFF action')
            off_action = self.api_call_prompt(config)
        else:
            off_action = ['ignore']

        return {'on': on_action, 'off': off_action}

    # Prompt user to select parameters for an individual API call
    # Called by api_target_rule_prompt for both on and off actions
    def api_call_prompt(self, config):
        # Read target node config file from disk
        config = self.load_config_from_ip(config['ip'])

        # Build options list from instances in target config file
        # Syntax: "device1 (dimmer)"
        options = [f'{i} ({config[i]["_type"]})' for i in config if is_device_or_sensor(i)]
        if 'ir_blaster' in config:
            options.append('IR Blaster')

        # Prompt user to select target instance, truncate _type param
        instance = questionary.select("Select target instance", choices=options).ask()
        instance = instance.split(" ")[0]

        # Prompt user to select API endpoint (options based on instance selection)
        if is_device(instance):
            endpoint = questionary.select("Select endpoint", choices=device_endpoints).ask()

        elif is_sensor(instance):
            # Remove trigger_sensor option if target does not support
            if config[instance]['_type'] in ['si7021', 'switch']:
                print("remove trigger_sensor")
                options = sensor_endpoints.copy()
                options.remove('trigger_sensor')
            else:
                options = sensor_endpoints
            endpoint = questionary.select("Select endpoint", choices=options).ask()

        elif instance == 'IR':
            target = questionary.select("Select IR target", choices=config['ir_blaster']['target']).ask()
            key = questionary.select("Select key", choices=ir_blaster_options[target]).ask()
            rule = ['ir_key', target, key]

        # Prompt user to add additional arg required by some endpoints
        if not instance == 'IR':
            rule = [endpoint, instance]

            if endpoint in ['enable_in', 'disable_in']:
                rule.append(questionary.text("Enter delay in seconds", validate=IntRange(1, 86400)).ask())
            elif endpoint == 'set_rule':
                # Call correct rule prompt for target instance type
                rule.append(self.schedule_rule_prompt_router(config[instance]))

        return rule

    # Takes IP, finds matching config path in existing_nodes dict, reads
    # config file and returns contents. Used by api_call_prompt to get
    # options, determine correct rule prompt, etc.
    def load_config_from_ip(self, ip):
        try:
            for i in self.existing_nodes:
                if self.existing_nodes[i]['ip'] == ip:
                    with open(self.existing_nodes[i]['config'], 'r') as file:
                        return json.load(file)
            else:
                raise FileNotFoundError
        except FileNotFoundError:
            print(f"\n{Fore.RED}FATAL ERROR{Fore.RESET}: Target node config file missing from disk")
            print("Unable to get options, please check the config path in cli_config.json")
            raise SystemExit

    # Iterate all configured sensors, display checkbox prompt for each
    # with all configured devices as options. Add all checked devices
    # to sensor targets list.
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
        rule = self.schedule_rule_prompt_router(config)
        config['schedule'][timestamp] = rule
        return config

    def schedule_rule_timestamp_prompt(self):
        return questionary.text("Enter timestamp (HH:MM)", validate=valid_timestamp).ask()

    def schedule_rule_timestamp_or_keyword_prompt(self):
        choice = questionary.select("\nTimestamp or keyword?", choices=['Timestamp', 'Keyword']).ask()
        if choice == 'Timestamp':
            return self.schedule_rule_timestamp_prompt()
        else:
            return questionary.select("\nSelect keyword", choices=self.schedule_keyword_options).ask()


if __name__ == '__main__':
    config = GenerateConfigFile()
    config.run_prompt()
    print(json.dumps(config.config, indent=4))
    config.write_to_disk()
