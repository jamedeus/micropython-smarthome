from .models import Node
from validation_constants import ir_blaster_options, device_endpoints, sensor_endpoints


# Helper function for get_api_target_menu_options, converts individual configs to frontend options
def convert_config_to_api_target_options(config):
    # Remove irrelevant sections
    del config['metadata']
    del config['wifi']

    # Result will contain 1 entry for each device, sensor, and ir_blaster in config
    result = {}
    for i in config:
        if i != "ir_blaster":
            # Instance string format: id-nickname (type)
            # Frontend splits, uses "nickname (type)" for dropdown option innerHTML, uses "id" for value
            # Backend only receives values (id) for config generation
            instance_string = f'{i}-{config[i]["nickname"]} ({config[i]["_type"]})'

            # All devices have same options
            if i.startswith("device"):
                result[instance_string] = device_endpoints

            # All sensors have same options except thermostat and switch (trigger unsupported)
            elif i.startswith("sensor") and config[i]["_type"] not in ["si7021", "switch"]:
                result[instance_string] = sensor_endpoints

            else:
                result[instance_string] = sensor_endpoints.copy()
                result[instance_string].remove('trigger_sensor')

        else:
            # Add options for all configured IR Blaster targets
            entry = {target: options for target, options in ir_blaster_options.items() if target in config[i]['target']}
            if entry:
                result["ir_blaster-Ir Blaster"] = entry

    return result


# Return dict with all existing nodes, their devices and sensors, and all API commands valid for each device/sensor type
# If friendly name of node passed as arg, name and IP are replaced with "self-target" and "127.0.0.1" respectively
# Used to populate cascading dropdown menu in frontend
def get_api_target_menu_options(editing_node=False):
    dropdownObject = {
        'addresses': {
            'self-target': '127.0.0.1'
        },
        'self-target': {}
    }

    for node in Node.objects.all():
        # Get option for each Node's config file
        entries = convert_config_to_api_target_options(node.config.config)

        # Skip if blank
        if entries == {}: continue

        # If config is currently being edited, add to self-target section
        if editing_node and node.friendly_name == editing_node:

            # Remove 'turn_on' and 'turn_off' from any api-target instances (prevent self-targeting in infinite loop)
            new_options = ['enable', 'disable', 'enable_in', 'disable_in', 'set_rule', 'reset_rule']
            entries = {key: (new_options if key.endswith('api-target)') else value) for key, value in entries.items()}

            dropdownObject["self-target"] = entries

            # Replace localhost (placeholder for new configs) with actual IP
            dropdownObject["addresses"]['self-target'] = node.ip

            # Add ignore option
            dropdownObject["self-target"]['ignore'] = {}

        # Otherwise add to main section, add IP to addresses
        else:
            dropdownObject[node.friendly_name] = entries
            dropdownObject['addresses'][node.friendly_name] = node.ip

            # Add ignore option
            dropdownObject[node.friendly_name]['ignore'] = {}

    return dropdownObject
