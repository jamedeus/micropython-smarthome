#!/usr/bin/python3

'''Command line utility used to control ESP32 nodes with API calls'''

import sys
import json
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

    # Get dict of existing node friendly names and IPs
    nodes = get_existing_nodes()

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


def main():
    '''Parses CLI arguments and makes API call, or prints help message'''

    # Remove name of application from args
    sys.argv.pop(0)

    # Parse args, send request if valid, pretty print response/error
    response = parse_ip(sys.argv)
    print(json.dumps(response, indent=4) + "\n")


if __name__ == "__main__":
    main()
