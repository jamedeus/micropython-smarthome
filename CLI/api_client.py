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
    'ir': {"Example usage": "./api_client.py ir [tv|ac|backlight] [command]"},
    # TODO fix these
    'condition_met': {"ERROR": "Must specify sensor"},
    'trigger_sensor': {"ERROR": "Must specify sensor"},
    'turn_on': {"ERROR": "Can only turn on/off devices, use enable/disable for sensors"},
    'turn_off': {"ERROR": "Can only turn on/off devices, use enable/disable for sensors"}
}


# Print all endpoints and descriptions, exit
def error():
    print("\n" + Fore.RED + "Error: please pass one of the following commands as argument:" + Fore.RESET + "\n")
    for command in endpoint_descriptions:
        print("- " + Fore.YELLOW + Style.BRIGHT + command.ljust(40) + Style.RESET_ALL + endpoint_descriptions[command])
    print()
    raise SystemExit


# Takes endpoint name, prints example (must be key in example_usage)
def print_example_usage(endpoint):
    try:
        return example_usage[endpoint]
    except KeyError:
        error()


# Entrypoint, find IP in CLI args, send remaining args to parse_command
def parse_ip(args):
    # Load config file
    try:
        with open(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'nodes.json'), 'r') as file:
            nodes = json.load(file)
    except FileNotFoundError:
        print("Warning: Unable to find nodes.json, friendly names will not work")
        nodes = {}

    # Get target ip
    for i in range(len(args)):

        if args[i] == "--all":
            args.pop(i)
            for i in nodes:
                ip = nodes[i]["ip"]
                print(ip)
                # Use copy of original args since items are removed by parser
                cmd = args.copy()
                response = parse_command(ip, cmd)
                print(json.dumps(response, indent=4) + "\n")
            return True

        elif args[i] in nodes:
            ip = nodes[args[i]]["ip"]
            args.pop(i)
            return parse_command(ip, args)

        elif args[i] == "-ip":
            args.pop(i)
            ip = args.pop(i)
            if valid_ip(ip):
                return parse_command(ip, args)
            else:
                print("Error: Invalid IP format")
                raise SystemExit

        elif valid_ip(args[i]):
            ip = args.pop(i)
            return parse_command(ip, args)

    else:
        print(Fore.RED + "Error: Must specify target ip, or one of the following names:" + Fore.RESET)
        for name in nodes:
            print(f" - {name}")
        raise SystemExit


# Iterate endpoints (see util/api_endpoints.py), find match, run
def parse_command(ip, args):
    if len(args) == 0:
        error()

    for endpoint in endpoints:
        if args[0] == endpoint[0]:
            # Remove endpoint arg
            match = args.pop(0)
            try:
                # Send remaining args to handler function
                return endpoint[1](ip, args)
            except SyntaxError:
                # No arguments given, show usage example
                return print_example_usage(match)
    else:
        error()


def main():
    # Remove name of application from args
    sys.argv.pop(0)

    # Parse args, send request if valid, pretty print response/error
    response = parse_ip(sys.argv)
    print(json.dumps(response, indent=4) + "\n")


if __name__ == "__main__":
    main()
