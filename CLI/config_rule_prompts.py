import json
import questionary
from colorama import Fore
from config_prompt_validators import IntRange, FloatRange
from validation_constants import ir_blaster_options, device_endpoints, sensor_endpoints
from helper_functions import (
    is_device,
    is_sensor,
    is_device_or_sensor,
    get_existing_nodes,
    get_device_and_sensor_manifests
)

# Map int rule limits to device/sensor types
# TODO integrate into manifest/metadata
rule_limits = {
    'dimmer': (1, 100),
    'bulb': (1, 100),
    'pwm': (0, 1023),
    'wled': (1, 255),
    'pir': (0, 60),
    'si7021': (65, 80),
    'load-cell': (0, 10000000)
}


# Reads all manifest files, returns mapping dict with config names as keys and
# rule prompt functions as values. All rule prompt functions accept config arg
# and rule type arg ("default" or "schedule"). The rule_type arg determines
# which options are shown (typically "default" ommits "Enabled" and "Disabled")
def build_rule_prompt_map():
    rule_prompt_map = {}

    # Get object containing all device and sensor manifest objects
    manifests = get_device_and_sensor_manifests()

    # Combine into single list
    manifests = manifests['devices'] + manifests['sensors']

    # Iterate manifest objects, add config_name as map key, prompt function as value
    for i in manifests:
        _type = i['config_name']
        prompt = i['rule_prompt']

        # Determine correct prompt functions using rule_prompt key
        if prompt == "int_range":
            rule_prompt_map[_type] = int_or_fade_rule_prompt
        elif prompt == "float_range":
            rule_prompt_map[_type] = float_rule_prompt
        elif prompt == "on_off":
            rule_prompt_map[_type] = on_off_rule_prompt
        elif prompt == "api_target":
            rule_prompt_map[_type] = api_target_rule_prompt
        else:
            rule_prompt_map[_type] = standard_rule_prompt

    return rule_prompt_map


# Takes partial config, runs appropriate default rule prompt for instance type, returns user selection
def default_rule_prompt_router(config):
    return rule_prompt_map[config['_type']](config, 'default')


# Takes partial config, runs appropriate schedule rule prompt for instance type, returns user selection
def schedule_rule_prompt_router(config):
    return rule_prompt_map[config['_type']](config, 'schedule')


# Rule prompt for instances that only support standard rules ("Enabled" and "Disabled")
# Same prompt for default and schedule rules
def standard_rule_prompt(config, rule_type):
    return questionary.select("Enter default rule", choices=['Enabled', 'Disabled']).ask()


# Rule prompt for instances that support "On" and "Off" in addition to standard rules
# Default prompt: Only show "On" and "Off" (standard rules are invalid)
# Schedule prompt: Show standard rules in addition to "On" and "Off"
def on_off_rule_prompt(config, rule_type):
    # Default rule prompt
    if rule_type == "default":
        return questionary.select("Enter default rule", choices=['On', 'Off']).ask()

    # Schedule rule prompt
    else:
        return questionary.select("Enter default rule", choices=['Enabled', 'Disabled', 'On', 'Off']).ask()


# Rule prompt for instances that support float rules in addition to standard rules
# Default prompt: Only show float prompt (standard rules are invalid)
# Schedule prompt: Show standard rules in addition to float
def float_rule_prompt(config, rule_type):
    minimum, maximum = rule_limits[config['_type']]

    # Default rule prompt
    if rule_type == "default":
        return questionary.text("Enter default rule", validate=FloatRange(minimum, maximum)).ask()

    # Schedule rule prompt
    else:
        choice = questionary.select("Select rule", choices=['Enabled', 'Disabled', 'Float']).ask()
        if choice == 'Float':
            return questionary.text("Enter rule", validate=FloatRange(minimum, maximum)).ask()
        else:
            return choice


# Rule prompt for DimmableLight subclasses (support int and fade rules in addition to standard)
# Default prompt: Require int rule (fade and standard are invalid)
# Schedule prompt: Show standard rules and fade prompt in addition to int
def int_or_fade_rule_prompt(config, rule_type):
    minimum = config['min_bright']
    maximum = config['max_bright']

    # Default rule prompt
    if rule_type == "default":
        return questionary.text("Enter default rule", validate=IntRange(minimum, maximum)).ask()

    # Schedule rule prompt
    else:
        choice = questionary.select("Select rule", choices=['Enabled', 'Disabled', 'Int', 'Fade']).ask()
        if choice == 'Int':
            return questionary.text("Enter rule", validate=IntRange(minimum, maximum)).ask()
        if choice == 'Fade':
            target = questionary.text("Enter target brightness", validate=IntRange(minimum, maximum)).ask()
            period = questionary.text("Enter duration in seconds", validate=IntRange(1, 86400)).ask()
            return f'fade/{target}/{period}'
        else:
            return choice


# Rule prompt used by ApiTarget device class (supports complicated dict rules)
# Default prompt: Go directly to API call rule prompt
# Schedule prompt: Give options for standard rules or API call rule
def api_target_rule_prompt(config, rule_type):
    # Default rule prompt
    if rule_type == "default":
        return api_call_rule_prompt(config)

    # Schedule rule prompt
    else:
        return api_target_schedule_rule_prompt(config)


# Shows standard rule options in addition to API call option
# Only used for schedule rules, enabled/disabled are invalid as default_rule
def api_target_schedule_rule_prompt(config):
    choice = questionary.select("Select rule", choices=['Enabled', 'Disabled', 'API Call']).ask()
    if choice == 'API Call':
        return api_call_rule_prompt(config)
    else:
        return choice


# Prompt user to select API call parameters for both ON and OFF actions
# Returns complete ApiTarget rule dict
def api_call_rule_prompt(config):
    if questionary.confirm("Should an API call be made when the device is turned ON?").ask():
        print('\nAPI Target ON action')
        on_action = api_call_prompt(config)
        print()
    else:
        on_action = ['ignore']

    if questionary.confirm("Should an API call be made when the device is turned OFF?").ask():
        print('\nAPI Target OFF action')
        off_action = api_call_prompt(config)
    else:
        off_action = ['ignore']

    return {'on': on_action, 'off': off_action}


# Prompt user to select parameters for an individual API call
# Called by api_call_rule_prompt for both on and off actions
def api_call_prompt(config):
    # Read target node config file from disk
    config = load_config_from_ip(config['ip'])

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
            rule.append(schedule_rule_prompt_router(config[instance]))

    return rule


# Takes IP, finds matching config path in existing_nodes dict, reads
# config file and returns contents. Used by api_call_prompt to get
# options, determine correct rule prompt, etc.
def load_config_from_ip(ip):
    existing_nodes = get_existing_nodes()
    try:
        for i in existing_nodes:
            if existing_nodes[i]['ip'] == ip:
                with open(existing_nodes[i]['config'], 'r') as file:
                    return json.load(file)
        else:
            raise FileNotFoundError
    except FileNotFoundError:
        print(f"\n{Fore.RED}FATAL ERROR{Fore.RESET}: Target node config file missing from disk")
        print("Unable to get options, please check the config path in cli_config.json")
        raise SystemExit


# Build mapping dict (must call after functions are declared)
rule_prompt_map = build_rule_prompt_map()
