#!/usr/bin/python3

'''Command line utility used to control ESP32 nodes with API calls'''

import sys
import json
import questionary
from colorama import Fore, Style
from api_endpoints import endpoint_map
from helper_functions import valid_ip, get_existing_nodes


# pylint: disable=line-too-long
# Used for help/error message
endpoint_descriptions = {
    "status":                                   "Get dict containing status of all devices and sensors",
    "reboot":                                   "Reboot the target node (will be unreachable for ~30 seconds)",
    "disable [target]":                         "Disable [target], can be device or sensor",
    "disable_in [target] [minutes]":            "Create timer to disable [target] in [minutes]",
    "enable [target]":                          "Enable [target], can be device or sensor",
    "enable_in [target] [minutes]":             "Create timer to enable [target] in [minutes]",
    "set_rule [target]":                        "Change [target]'s current rule (until next rule change), can be device or sensor",
    "increment_rule [target] [amount]":         "Increment [target]'s current rule by [amount] (must be int)",
    "reset_rule [target]":                      "Replace [target]'s current rule with scheduled rule, used to undo set_rule",
    "reset_all_rules":                          "Replace current rules of all devices and sensors with their scheduled rule",
    "get_schedule_rules [target]":              "View schedule rules for [target], can be device or sensor",
    "add_rule [target] [HH:MM] [rule]":         "Add schedule rule, will persist until next reboot",
    "remove_rule [target] [HH:MM]":             "Remove an existing schedule rule until next reboot",
    "save_rules":                               "Write current schedule rules to disk, persists after reboot",
    "get_schedule_keywords ":                   "View schedule keywords and the timestamps they represent",
    "add_schedule_keyword [keyword] [HH:MM]":   "Add [keyword] representing timestamp, can be used in schedule rules",
    "remove_schedule_keyword [keyword]":        "Remove [keyword], deletes all associated schedule rules from queue",
    "save_schedule_keywords":                   "Write current schedule keywords to disk, persists after reboot",
    "get_attributes [target]":                  "View all of [target]'s attributes, can be device or sensor",
    "condition_met [sensor]":                   "Check if [sensor]'s condition is met (turns on target devices)",
    "trigger_sensor [sensor]":                  "Simulates the sensor being triggered (turns on target devices)",
    "turn_on [device]":                         "Turn the device on (loop may undo in some situations, disable sensor to prevent)",
    "turn_off [device]":                        "Turn the device off (loop may undo in some situations, disable sensor to prevent)",
    "ir [target] [key]":                         "Simulate 'key' being pressed on remote control for 'target' (can be tv or ac)",
    "ir_get_existing_macros":                   "Get dict of existing IR macros",
    "ir_create_macro [name]":                   "Create a new macro (use ir_add_macro_action to populate actions)",
    "ir_delete_macro [name]":                   "Delete an existing macro 'name'",
    "ir_add_macro_action [name] [target] [key]":"""Append action to macro 'name' simulating pressing 'key' on remote control for 'target'
                                            Optional: 'delay' arg (ms delay after key), 'repeats' arg (number of times to press key)""",
    "ir_run_macro [name]":                      "Run all actions in an existing macro 'name'",
    "get_temp":                                 "Get current reading from temp sensor in Farenheit",
    "get_humid":                                "Get current relative humidity from temp sensor",
    "get_climate":                              "Get current temp and humidity from sensor",
    "set_gps_coords":                           "Set the latitude and longitude used to look up sunrise/sunset times",
    "clear_log":                                "Delete node's log file"
}


# Example CLI usage for each endpoint, shown when arguments are missing
example_usage = {
    'disable': {"Example usage": "./api_client.py disable [device|sensor]"},
    'disable_in': {"Example usage": "./api_client.py disable_in [device|sensor] [minutes]"},
    'enable': {"Example usage": "./api_client.py enable [device|sensor]"},
    'enable_in': {"Example usage": "./api_client.py enable_in [device|sensor] [minutes]"},
    'set_rule': {"Example usage": "./api_client.py set_rule [device|sensor] [rule]"},
    'increment_rule': {"Example usage": "./api_client.py increment_rule [device] [int]"},
    'reset_rule': {"Example usage": "./api_client.py reset_rule [device|sensor]"},
    'get_schedule_rules': {"Example usage": "./api_client.py get_schedule_rules [device|sensor]"},
    'add_rule': {"Example usage": "./api_client.py add_rule [device|sensor] [HH:MM] [rule] <overwrite>"},
    'remove_rule': {"Example usage": "./api_client.py remove_rule [device|sensor] [HH:MM]"},
    'add_schedule_keyword': {"Example usage": "./api_client.py add_schedule_keyword [keyword] [HH:MM]"},
    'remove_schedule_keyword': {"Example usage": "./api_client.py remove_schedule_keyword [keyword]"},
    'get_attributes': {"Example usage": "./api_client.py get_attributes [device|sensor]"},
    'condition_met': {"Example usage": "./api_client.py condition_met [sensor]"},
    'trigger_sensor': {"Example usage": "./api_client.py trigger_sensor [sensor]"},
    'turn_on': {"Example usage": "./api_client.py turn_on [device]"},
    'turn_off': {"Example usage": "./api_client.py turn_off [device]"},
    'ir': {"Example usage": "./api_client.py ir [tv|ac] [command]"},
    'ir_create_macro': {"Example usage": "./api_client.py ir_create_macro [name]"},
    'ir_delete_macro': {"Example usage": "./api_client.py ir_delete_macro [name]"},
    'ir_add_macro_action': {"Example usage": "./api_client.py ir_add_macro_action [name] [target] [key] <delay> <repeats>"},
    'ir_run_macro': {"Example usage": "./api_client.py ir_run_macro [name]"},
    'set_gps_coords': {"Example usage": "./api_client.py set_gps_coords [latitude] [longitude]"},
}
# pylint: enable=line-too-long


# Get dict of existing node friendly names and IPs from cli_config.json
nodes = get_existing_nodes()


def endpoint_error():
    '''Prints all endpoints and descriptions then exits script'''
    print(
        "\n" + Fore.RED +
        "Error: please pass one of the following commands as argument:" +
        Fore.RESET + "\n")
    for command, description in endpoint_descriptions.items():
        print(
            "- " + Fore.YELLOW + Style.BRIGHT +
            command.ljust(42) +
            Style.RESET_ALL + description
        )
    print()
    raise SystemExit


def example_usage_error(endpoint):
    '''Takes endpoint name, prints usage example, exits script.
    If endpoint is invalid, print all endpoints and their descriptions.
    '''
    try:
        return example_usage[endpoint]
    except KeyError:
        return endpoint_error()


def missing_target_error(nodes):
    '''Prints available nodes from cli_config.json then exits scrip.
    Called when no target IP/node is given, or invalid node is given.
    '''
    print(
        Fore.RED +
        "Error: Must specify target ip, or one of the following names:" +
        Fore.RESET
    )
    for name in nodes:
        print(f" - {name}")
    raise SystemExit


def parse_ip(args):
    '''Receives command line args, finds IP arg (or IP of node if node name
    given), passes IP and remaining args to parse_command (makes API call).
    '''

    # Parse target IP from args, pass IP + remaining args to parse_command
    for i, arg in enumerate(args):

        # User passed --all flag, iterate existing nodes and pass args to each
        if arg == "--all":
            args.pop(i)
            for i in nodes:
                ip = nodes[i]
                print(f"{i} ({ip})")
                # Use copy to preserve args for next node (parse_command removes endpoint)
                cmd = args.copy()
                response = parse_command(ip, cmd)
                print(json.dumps(response, indent=4) + "\n")
            print("Done\n")
            raise SystemExit

        # User passed node name, look up IP in dict
        if arg in nodes:
            ip = nodes[arg]
            args.pop(i)
            return parse_command(ip, args)

        # User passed IP flag
        if arg == "-ip":
            args.pop(i)
            ip = args.pop(i)
            if valid_ip(ip):
                return parse_command(ip, args)
            print("Error: Invalid IP format")
            raise SystemExit

        # User passed IP with no flag
        if valid_ip(arg):
            ip = args.pop(i)
            return parse_command(ip, args)

    # No IP or node name found
    return missing_target_error(nodes)


def parse_command(ip, args):
    '''Takes target IP and list of command args (first must be endpoint name).
    Finds matching endpoint, calls handler function with remaining args.
    '''

    if len(args) == 0:
        endpoint_error()

    endpoint = args[0]
    args = args[1:]

    try:
        return endpoint_map[endpoint](ip, args)
    except SyntaxError:
        # No arguments given, show usage example
        return example_usage_error(endpoint)
    except KeyError:
        return endpoint_error()


def api_target_node_prompt():
    '''Prompts user to select a Node for api_prompt'''

    node_options = list(nodes.keys())
    node_options.append('Done')

    return questionary.select(
        "Select target node",
        choices=node_options
    ).unsafe_ask()


def api_prompt():
    '''Prompt allows user to send API commands to existing nodes'''

    # Prompt to select existing node, get name and IP address
    node = api_target_node_prompt()
    if node == 'Done':
        return
    node_ip = nodes[node]

    # Get API endpoint options, add Done (break loop)
    endpoint_options = list(example_usage.keys())
    endpoint_options.append('Done')

    while True:
        # Get status object, print current status (repeats after each command)
        status = parse_command(node_ip, ['status'])
        print(f'{node} status:')
        print(json.dumps(status, indent=4))

        # Prompt to select endpoint
        endpoint = questionary.select(
            "Select command",
            choices=endpoint_options
        ).unsafe_ask()

        # Create list with endpoint as first arg
        # Prompts below add additional args (if needed), result sent to node
        command_args = [endpoint]

        # Break loop when user selects Done
        if endpoint == 'Done':
            break

        # If selected endpoint requires device/sensor argument
        if endpoint in [
            'disable',
            'disable_in',
            'enable',
            'enable_in',
            'set_rule',
            'increment_rule',
            'reset_rule',
            'get_schedule_rules',
            'add_rule',
            'remove_rule',
            'get_attributes'
        ]:
            # Prompt to select from available devices and sensors
            target = questionary.select(
                "Select device or sensor",
                choices=list(status['devices'].keys()) + list(status['sensors'].keys())
            ).unsafe_ask()
            command_args.append(target)

            # If selected endpoint requires additional arg
            if endpoint in ['disable_in', 'enable_in']:
                arg = questionary.text(
                    "Enter delay (minutes):"
                ).unsafe_ask()
                command_args.append(arg)

            elif endpoint == 'set_rule':
                arg = questionary.text(
                    "Enter rule"
                ).unsafe_ask()
                command_args.append(arg)

            elif endpoint == 'increment_rule':
                arg = questionary.text(
                    "Enter amount to increment rule by (can be negative)"
                ).unsafe_ask()
                command_args.append(arg)

            elif endpoint == 'add_rule':
                # Prompt to enter timestamp or keyword
                timestamp = questionary.text(
                    "Enter timestamp (HH:MM) or keyword"
                ).unsafe_ask()
                command_args.append(timestamp)

                # Prompt to enter rule
                rule = questionary.text(
                    "Enter rule"
                ).unsafe_ask()
                command_args.append(rule)

            elif endpoint == 'remove_rule':
                # Get list of existing rules for target
                if target.startswith('device'):
                    rules = list(status['devices'][target]['schedule'].keys())
                else:
                    rules = list(status['sensors'][target]['schedule'].keys())

                # Prompt to select existing rule to remove
                rule = questionary.select(
                    'Select rule to remove',
                    choices=rules
                ).unsafe_ask()
                command_args.append(rule)

        # If selected endpoint requires device argument
        elif endpoint in ['turn_on', 'turn_off']:
            # Prompt to select from available devices
            target = questionary.select(
                "Select device or sensor",
                choices=list(status['devices'].keys())
            ).unsafe_ask()
            command_args.append(target)

        elif endpoint in ['trigger_sensor', 'condition_met']:
            # Prompt to select from available sensors
            target = questionary.select(
                "Select device or sensor",
                choices=list(status['sensors'].keys())
            ).unsafe_ask()
            command_args.append(target)

        elif endpoint == 'add_schedule_keyword':
            # Prompt user to enter keyword and timestamp
            keyword = questionary.text(
                'Enter new keyword name'
            ).unsafe_ask()
            command_args.append(keyword)

            timestamp = questionary.text(
                'Enter new keyword timestamp'
            ).unsafe_ask()
            command_args.append(timestamp)

        elif endpoint == 'remove_schedule_keyword':
            # Prompt user to select existing keyword to delete
            keyword = questionary.select(
                'Select keyword to delete',
                choices=list(status['metadata']['schedule_keywords'])
            ).unsafe_ask()
            command_args.append(keyword)

        elif endpoint == 'ir_create_macro':
            # Prompt user for new macro name
            arg = questionary.text(
                'Enter new macro name'
            ).unsafe_ask()
            command_args.append(arg)

        elif endpoint == 'set_gps_coords':
            # Prompt user for longitude and latitude
            latitude = questionary.text(
                'Enter latitude'
            ).unsafe_ask()
            command_args.append(latitude)

            longitude = questionary.text(
                'Enter longitude'
            ).unsafe_ask()
            command_args.append(longitude)

        # Send command, print response
        response = parse_command(node_ip, command_args)
        print(json.dumps(response, indent=4))
        questionary.press_any_key_to_continue().ask()


def main():
    '''Parses CLI arguments and makes API call, or prints help message'''

    # Remove name of application from args
    sys.argv.pop(0)

    # Show interactive prompt if no args
    if len(sys.argv) == 0:
        try:
            api_prompt()
        except KeyboardInterrupt as interrupt:
            raise SystemExit from interrupt

    else:
        # Parse args, send request if valid, pretty print response/error
        response = parse_ip(sys.argv)
        print(json.dumps(response, indent=4) + "\n")


if __name__ == "__main__":
    main()
