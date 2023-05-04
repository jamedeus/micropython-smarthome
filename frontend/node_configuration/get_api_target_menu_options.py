from .models import Node


# Options for each supported IR Blaster target device, used to populate ApiTarget menu
ir_blaster_options = {
    "tv": ['power', 'vol_up', 'vol_down', 'mute', 'up', 'down', 'left', 'right', 'enter', 'settings', 'exit', 'source'],
    "ac": ['start', 'stop', 'off']
}


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
            instance_string = f'{i}-{config[i]["nickname"]} ({config[i]["type"]})'

            # All devices have same options
            if i.startswith("device"):
                result[instance_string] = ['enable', 'disable', 'enable_in', 'disable_in', 'set_rule', 'reset_rule', 'turn_on', 'turn_off']

            # All sensors have same options except thermostat and switch (trigger unsupported)
            elif i.startswith("sensor") and not (config[i]["type"] == "si7021" or config[i]["type"] == "switch"):
                result[instance_string] = ['enable', 'disable', 'enable_in', 'disable_in', 'set_rule', 'reset_rule', 'trigger_sensor']
            else:
                result[instance_string] = ['enable', 'disable', 'enable_in', 'disable_in', 'set_rule', 'reset_rule']
        else:
            # Add options for all configured IR Blaster targets
            entry = {target: options for target, options in ir_blaster_options.items() if target in config[i]['target']}
            if entry:
                result["ir_blaster-Ir Blaster"] = entry

    return result


# Return dict with all configured nodes, their devices and sensors, and API commands which target each device/sensor type
# If friendly name of existing node passed as arg, name and IP are replaced with "self-target" and "127.0.0.1" respectively
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
            entries = {key: new_options for key, value in entries.items() if key.endswith('api-target)')}

            dropdownObject["self-target"] = entries

        # Otherwise add to main section, add IP to addresses
        else:
            dropdownObject[node.friendly_name] = entries
            dropdownObject['addresses'][node.friendly_name] = node.ip

    return dropdownObject
