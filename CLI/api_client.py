#!/usr/bin/python3

import os
import sys
import json
from colorama import Fore, Style
from helper_functions import valid_ip
from api_endpoints import endpoints


# Used for help/error message
endpoint_descriptions = {
    "status":                                "Get dict containing status of all devices and sensors",
    "reboot":                                "Reboot the target node (will be unreachable for ~30 seconds)",
    "disable [target]":                      "Disable [target], can be device or sensor",
    "disable_in [target] [minutes]":         "Create timer to disable [target] in [minutes]",
    "enable [target]":                       "Enable [target], can be device or sensor",
    "enable_in [target] [minutes]":          "Create timer to enable [target] in [minutes]",
    "set_rule [target]":                     "Change [target]'s current rule (until next rule change), can be device or sensor",
    "reset_rule [target]":                   "Replace [target]'s current rule with scheduled rule, used to undo set_rule",
    "reset_all_rules":                       "Replace current rules of all devices and sensors with their scheduled rule",
    "get_schedule_rules [target]":           "View schedule rules for [target], can be device or sensor",
    "add_rule [target] [HH:MM] [rule]":      "Add schedule rule, will persist until next reboot",
    "remove_rule [target] [HH:MM]":          "Remove an existing schedule rule until next reboot",
    "save_rules":                            "Write current schedule rules to disk, persists after reboot",
    "get_schedule_keywords ":                "View schedule keywords and the timestamps they represent",
    "add_schedule_keyword [keyword] [HH:MM]":"Add [keyword] representing timestamp, can be used in schedule rules",
    "remove_schedule_keyword [keyword]":     "Remove [keyword], deletes all associated schedule rules from queue",
    "save_schedule_keywords":                "Write current schedule keywords to disk, persists after reboot",
    "get_attributes [target]":               "View all of [target]'s attributes, can be device or sensor",
    "condition_met [sensor]":                "Check if [sensor]'s condition is met (turns on target devices)",
    "trigger_sensor [sensor]":               "Simulates the sensor being triggered (turns on target devices)",
    "turn_on [device]":                      "Turn the device on (loop may undo in some situations, disable sensor to prevent)",
    "turn_off [device]":                     "Turn the device off (loop may undo in some situations, disable sensor to prevent)",
    "ir [target||key]":                      "Simulate 'key' being pressed on remote control for 'target' (can be tv or ac)",
    "get_temp":                              "Get current reading from temp sensor in Farenheit",
    "get_humid":                             "Get current relative humidity from temp sensor",
    "get_climate":                           "Get current temp and humidity from sensor",
    "clear_log":                             "Delete node's log file"
}


# Example CLI usage for each endpoint, shown when arguments are missing
example_usage = {
    'disable': {"Example usage": "./api_client.py disable [device|sensor]"},
    'disable_in': {"Example usage": "./api_client.py disable_in [device|sensor] [minutes]"},
    'enable': {"Example usage": "./api_client.py enable [device|sensor]"},
    'enable_in': {"Example usage": "./api_client.py enable_in [device|sensor] [minutes]"},
    'set_rule': {"Example usage": "./api_client.py set_rule [device|sensor] [rule]"},
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
    'ir': {"Example usage": "./api_client.py ir [tv|ac|backlight] [command]"}
}


# Print all endpoints and descriptions, exit
def endpoint_error():
    print("\n" + Fore.RED + "Error: please pass one of the following commands as argument:" + Fore.RESET + "\n")
    for command in endpoint_descriptions:
        print("- " + Fore.YELLOW + Style.BRIGHT + command.ljust(40) + Style.RESET_ALL + endpoint_descriptions[command])
    print()
    raise SystemExit


# Takes endpoint name, prints example (must be key in example_usage)
def example_usage_error(endpoint):
    try:
        return example_usage[endpoint]
    except KeyError:
        endpoint_error()


# Show available nodes and exit, called when no target IP/node in args
def missing_target_error(nodes):
    print(Fore.RED + "Error: Must specify target ip, or one of the following names:" + Fore.RESET)
    for name in nodes:
        print(f" - {name}")
    raise SystemExit


# Load nodes.json, return dict with friendly names and IPs of existing nodes
def load_config_file():
    try:
        with open(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'nodes.json'), 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        print("Warning: Unable to find nodes.json, friendly names will not work")
        return {}


# Receives args, finds IP, passes IP + remaining args to parse_command
def parse_ip(args):
    # Get dict of existing node friendly names and IPs
    nodes = load_config_file()

    # Parse target IP from args, pass IP + remaining args to parse_command
    for i in range(len(args)):

        # User passed --all flag, iterate existing nodes and pass args to each
        if args[i] == "--all":
            args.pop(i)
            for i in nodes:
                ip = nodes[i]["ip"]
                print(f"{i} ({ip})")
                # Use copy to preserve args for next node (parse_command removes endpoint)
                cmd = args.copy()
                response = parse_command(ip, cmd)
                print(json.dumps(response, indent=4) + "\n")
            print("Done\n")
            raise SystemExit

        # User passed node name, look up IP in dict
        elif args[i] in nodes:
            ip = nodes[args[i]]["ip"]
            args.pop(i)
            return parse_command(ip, args)

        # User passed IP flag
        elif args[i] == "-ip":
            args.pop(i)
            ip = args.pop(i)
            if valid_ip(ip):
                return parse_command(ip, args)
            else:
                print("Error: Invalid IP format")
                raise SystemExit

        # User passed IP with no flag
        elif valid_ip(args[i]):
            ip = args.pop(i)
            return parse_command(ip, args)

    # No IP or node name found
    else:
        missing_target_error(nodes)


# Takes target IP + args
# Iterate endpoints (see util/api_endpoints.py) until match found in args, run
def parse_command(ip, args):
    if len(args) == 0:
        endpoint_error()

    for endpoint in endpoints:
        if args[0] == endpoint[0]:
            # Remove endpoint arg
            match = args.pop(0)
            try:
                # Send remaining args to handler function
                return endpoint[1](ip, args)
            except SyntaxError:
                # No arguments given, show usage example
                return example_usage_error(match)
    else:
        endpoint_error()


def main():
    # Remove name of application from args
    sys.argv.pop(0)

    # Parse args, send request if valid, pretty print response/error
    response = parse_ip(sys.argv)
    print(json.dumps(response, indent=4) + "\n")


if __name__ == "__main__":
    main()
