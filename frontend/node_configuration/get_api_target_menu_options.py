'''Functions used to generate menu options for ApiTargetRuleModal dropdowns'''

from helper_functions import get_device_and_sensor_metadata
from validation_constants import ir_blaster_options, device_endpoints, sensor_endpoints
from .models import Node

# Get object containing all device/sensor metadata
metadata = get_device_and_sensor_metadata()


def get_metadata_section(category, _type):
    '''Takes category (devices or sensors) and type, returns metadata section'''
    for i in metadata[category]:
        if i['config_name'] == _type:
            return i


def convert_config_to_api_target_options(config):
    '''Helper function for get_api_target_menu_options.
    Takes full config, returns frontend options.
    '''

    # Result will contain 1 entry for each device, sensor, and ir_blaster in config
    result = {}
    for i in config:
        # All devices have same options
        if i.startswith("device"):
            result[i] = {
                "display": f'{config[i]["nickname"]} ({config[i]["_type"]})',
                "options": device_endpoints
            }

        # All sensors have same options except thermostat and switch (trigger unsupported)
        elif i.startswith("sensor"):
            result[i] = {
                "display": f'{config[i]["nickname"]} ({config[i]["_type"]})',
                "options": sensor_endpoints.copy()
            }

            # Remove trigger endpoint if sensor is not triggerable
            sensor_metadata = get_metadata_section("sensors", config[i]["_type"])
            if not sensor_metadata["triggerable"]:
                result[i]["options"].remove("trigger_sensor")

        elif i == "ir_blaster":
            # Add options for all configured IR Blaster targets
            entry = {target: options for target, options in ir_blaster_options.items()
                     if target in config[i]['target']}
            if entry:
                result["ir_key"] = {
                    "display": "Ir Blaster",
                    "options": [target for target in ir_blaster_options
                                if target in config[i]['target']],
                    "keys": {target: value for target, value in entry.items()
                             if target in config[i]['target']}
                }

    return result


def get_api_target_menu_options(editing_node=False):
    '''Returns object used to populate ApiTargetRuleModal cascading dropdown menu.
    Contains all existing nodes and valid API commands for each device/sensor of each node.
    Passing node friendly name as arg replaces its name and IP with "self-target" and "127.0.0.1".
    '''

    dropdown_object = {
        'addresses': {
            'self-target': '127.0.0.1'
        },
        'self-target': {}
    }

    for node in Node.objects.all():
        # Get option for each Node's config file
        entries = convert_config_to_api_target_options(node.config.config)

        # Skip if blank
        if not entries:
            continue

        # If config is currently being edited, add to self-target section
        if editing_node and node.friendly_name == editing_node:
            # Remove 'turn_on' and 'turn_off' from any api-target instances
            # (prevent self-targeting in infinite loop)
            new_options = ['enable', 'disable', 'enable_in', 'disable_in', 'set_rule', 'reset_rule']
            for instance in entries.values():
                if instance['display'].endswith('api-target)'):
                    instance['options'] = new_options

            dropdown_object["self-target"] = entries

            # Replace localhost (placeholder for new configs) with actual IP
            dropdown_object["addresses"]['self-target'] = node.ip

            # Add ignore option
            dropdown_object["self-target"]['ignore'] = {
                'display': 'Ignore action'
            }

        # Otherwise add to main section, add IP to addresses
        else:
            dropdown_object[node.friendly_name] = entries
            dropdown_object['addresses'][node.friendly_name] = node.ip

            # Add ignore option
            dropdown_object[node.friendly_name]['ignore'] = {
                'display': 'Ignore action'
            }

    return dropdown_object
