#!/usr/bin/python3

import os
import sys
import json
import asyncio
import re
from colorama import Fore, Style

timestamp_regex = r'^([0-1][0-9]|2[0-3]):[0-5][0-9]$'
ip_regex = r'^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'

# Valid IR commands for each target, used in error message
ir_commands = {
    "tv": "power, vol_up, vol_down, mute, up, down, left, right, enter, settings, exit, source",
    "ac": "ON, OFF, UP, DOWN, FAN, TIMER, UNITS, MODE, STOP, START"
}

usage_examples = {
    "status":                           "Get dict containing status of all devices and sensors",
    "disable [target]":                 "Disable [target], can be device or sensor",
    "disable_in [target] [minutes]":    "Create timer to disable [target] in [minutes]",
    "enable [target]":                  "Enable [target], can be device or sensor",
    "enable_in [target] [minutes]":     "Create timer to enable [target] in [minutes]",
    "set_rule [target]":                "Change [target]'s current rule, can be device or sensor, lasts until next rule change",
    "reset_rule [target]":              "Replace [target]'s current rule with scheduled rule, used to undo set_rule",
    "reset_all_rules":                  "Replace current rules of all devices and sensors with their scheduled rule",
    "get_schedule_rules [target]":      "View schedule rules for [target], can be device or sensor",
    "add_rule [target] [HH:MM] [rule]": "Add schedule rule, will persist until next reboot",
    "remove_rule [target] [HH:MM]":     "Remove an existing schedule rule until next reboot",
    "save_rules":                       "Write current schedule rules to disk, persists after reboot",
    "get_attributes [target]":          "View all of [target]'s attributes, can be device or sensor",
    "condition_met [sensor]":           "Check if [sensor]'s condition is met (turns on target devices)",
    "trigger_sensor [sensor]":          "Simulates the sensor being triggered (turns on target devices)",
    "turn_on [device]":                 "Turn the device on (note: loop may undo in some situations, disable sensor to prevent)",
    "turn_off [device]":                "Turn the device off (note: loop may undo in some situations, disable sensor to prevent)",
    "ir [target||key]":                 "Simulate 'key' being pressed on remote control for 'target' (target can be tv or ac)",
    "get_temp":                         "Get current reading from temp sensor in Farenheit",
    "get_humid":                        "Get current relative humidity from temp sensor",
    "get_climate":                      "Get current temp and humidity from sensor",
    "clear_log":                        "Delete node's log file"
}


def error():
    print("\n" + Fore.RED + "Error: please pass one of the following commands as argument:" + Fore.RESET + "\n")
    for command in usage_examples:
        print("- " + Fore.YELLOW + Style.BRIGHT + command.ljust(35) + Style.RESET_ALL + usage_examples[command])
    print()
    raise SystemExit


async def request(ip, msg):
    reader, writer = await asyncio.open_connection(ip, 8123)
    try:
        writer.write('{}\n'.format(json.dumps(msg)).encode())
        await writer.drain()
        res = await reader.read()
    except OSError:
        return "Error: Request failed"
    try:
        response = json.loads(res)
    except ValueError:
        return "Error: Unable to decode response"
    writer.close()
    await writer.wait_closed()

    return response


def parse_ip(args):
    # Load config file
    try:
        with open(os.path.dirname(os.path.realpath(__file__)) + '/nodes.json', 'r') as file:
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
            if re.match(ip_regex, ip):
                return parse_command(ip, args)
            else:
                print("Error: Invalid IP format")
                raise SystemExit

        elif re.match(ip_regex, args[i]):
            ip = args.pop(i)
            return parse_command(ip, args)

    else:
        print(Fore.RED + "Error: Must specify target ip, or one of the following names:" + Fore.RESET)
        for name in nodes:
            print(f" - {name}")
        raise SystemExit


def parse_command(ip, args):
    if len(args) == 0:
        error()

    for endpoint in endpoints:
        if args[0] == endpoint[0]:
            # Remove endpoint arg
            args.pop(0)
            # Send remaining args to handler function
            return endpoint[1](ip, args)

    else:
        error()


# Populated with endpoint:handler pairs by decorators below
endpoints = []


def add_endpoint(url):
    def _add_endpoint(func):
        endpoints.append((url, func))
        return func
    return _add_endpoint


@add_endpoint("status")
def status(ip, params):
    return asyncio.run(request(ip, ['status']))


@add_endpoint("reboot")
def reboot(ip, params):
    return asyncio.run(request(ip, ['reboot']))


@add_endpoint("disable")
def disable(ip, params):
    if len(params) == 0:
        return {"Example usage": "./api_client.py disable [device|sensor]"}

    if params[0].startswith("sensor") or params[0].startswith("device"):
        return asyncio.run(request(ip, ['disable', params[0]]))
    else:
        return {"ERROR": "Can only disable devices and sensors"}


@add_endpoint("disable_in")
def disable_in(ip, params):
    if len(params) == 0:
        return {"Example usage": "./api_client.py disable_in [device|sensor] [minutes]"}

    if params[0].startswith("sensor") or params[0].startswith("device"):
        target = params.pop(0)
        try:
            period = float(params[0])
            return asyncio.run(request(ip, ['disable_in', target, period]))
        except IndexError:
            return {"ERROR": "Please specify delay in minutes"}
    else:
        return {"ERROR": "Can only disable devices and sensors"}


@add_endpoint("enable")
def enable(ip, params):
    if len(params) == 0:
        return {"Example usage": "./api_client.py enable [device|sensor]"}

    if params[0].startswith("sensor") or params[0].startswith("device"):
        return asyncio.run(request(ip, ['enable', params[0]]))
    else:
        return {"ERROR": "Can only enable devices and sensors"}


@add_endpoint("enable_in")
def enable_in(ip, params):
    if len(params) == 0:
        return {"Example usage": "./api_client.py enable_in [device|sensor] [minutes]"}

    if params[0].startswith("sensor") or params[0].startswith("device"):
        target = params.pop(0)
        try:
            period = float(params[0])
            return asyncio.run(request(ip, ['enable_in', target, period]))
        except IndexError:
            return {"ERROR": "Please specify delay in minutes"}
    else:
        return {"ERROR": "Can only enable devices and sensors"}


@add_endpoint("set_rule")
def set_rule(ip, params):
    if len(params) == 0:
        return {"Example usage": "./api_client.py set_rule [device|sensor] [rule]"}

    if params[0].startswith("sensor") or params[0].startswith("device"):
        target = params.pop(0)
        try:
            return asyncio.run(request(ip, ['set_rule', target, params[0]]))
        except IndexError:
            return {"ERROR": "Must specify new rule"}
    else:
        return {"ERROR": "Can only set rules for devices and sensors"}


@add_endpoint("reset_rule")
def reset_rule(ip, params):
    if len(params) == 0:
        return {"Example usage": "./api_client.py reset_rule [device|sensor]"}

    if params[0].startswith("sensor") or params[0].startswith("device"):
        target = params.pop(0)
        return asyncio.run(request(ip, ['reset_rule', target]))
    else:
        return {"ERROR": "Can only set rules for devices and sensors"}


@add_endpoint("reset_all_rules")
def reset_all_rules(ip, params):
    return asyncio.run(request(ip, ['reset_all_rules']))


@add_endpoint("get_schedule_rules")
def get_schedule_rules(ip, params):
    if len(params) == 0:
        return {"Example usage": "./api_client.py get_schedule_rules [device|sensor]"}

    if params[0].startswith("sensor") or params[0].startswith("device"):
        target = params.pop(0)
        return asyncio.run(request(ip, ['get_schedule_rules', target]))
    else:
        return {"ERROR": "Only devices and sensors have schedule rules"}


@add_endpoint("add_rule")
def add_schedule_rule(ip, params):
    if len(params) == 0:
        return {"Example usage": "./api_client.py add_rule [device|sensor] [HH:MM] [rule] <overwrite>"}

    if params[0].startswith("sensor") or params[0].startswith("device"):
        target = params.pop(0)
    else:
        return {"ERROR": "Only devices and sensors have schedule rules"}

    if len(params) < 2:
        return {"ERROR": "Must specify timestamp/keyword followed by rule"}
    else:
        timestamp = params.pop(0)

    cmd = ['add_schedule_rule', target, timestamp]

    # Add remaining args to cmd - may contain rule, or rule + overwrite
    for i in params:
        cmd.append(i)

    return asyncio.run(request(ip, cmd))


@add_endpoint("remove_rule")
def remove_rule(ip, params):
    if len(params) == 0:
        return {"Example usage": "./api_client.py remove_rule [device|sensor] [HH:MM]"}

    if params[0].startswith("sensor") or params[0].startswith("device"):
        target = params.pop(0)
    else:
        return {"ERROR": "Only devices and sensors have schedule rules"}

    if len(params) < 1:
        return {"ERROR": "Must specify timestamp/keyword followed by rule"}
    else:
        timestamp = params.pop(0)

    return asyncio.run(request(ip, ['remove_rule', target, timestamp]))


@add_endpoint("save_rules")
def save_rules(ip, params):
    return asyncio.run(request(ip, ['save_rules']))


@add_endpoint("get_schedule_keywords")
def get_schedule_keywords(ip, params):
    return asyncio.run(request(ip, ['get_schedule_keywords']))


@add_endpoint("add_schedule_keyword")
def add_schedule_keyword(ip, params):
    if len(params) == 0:
        return {"Example usage": "./api_client.py add_schedule_keyword [keyword] [HH:MM]"}

    keyword = params.pop(0)

    if len(params) > 0 and re.match(timestamp_regex, params[0]):
        timestamp = params.pop(0)
    else:
        return {"ERROR": "Timestamp format must be HH:MM (no AM/PM)"}

    cmd = ['add_schedule_keyword', {keyword: timestamp}]

    return asyncio.run(request(ip, cmd))


@add_endpoint("remove_schedule_keyword")
def remove_schedule_keyword(ip, params):
    if len(params) == 0:
        return {"Example usage": "./api_client.py remove_schedule_keyword [keyword]"}

    cmd = ['remove_schedule_keyword', params.pop(0)]
    return asyncio.run(request(ip, cmd))


@add_endpoint("save_schedule_keywords")
def save_schedule_keywords(ip, params):
    return asyncio.run(request(ip, ['save_schedule_keywords']))


@add_endpoint("get_attributes")
def get_attributes(ip, params):
    if len(params) == 0:
        return {"Example usage": "./api_client.py get_attributes [device|sensor]"}

    if params[0].startswith("sensor") or params[0].startswith("device"):
        target = params.pop(0)
        return asyncio.run(request(ip, ['get_attributes', target]))
    else:
        return {"ERROR": "Must specify device or sensor"}


@add_endpoint("ir")
def ir(ip, params):
    if len(params) > 0 and (params[0] == "tv" or params[0] == "ac"):
        target = params.pop(0)
        try:
            return asyncio.run(request(ip, ['ir_key', target, params[0]]))
        except IndexError:
            return {"ERROR": f"Must speficy one of the following commands: {ir_commands[target]}"}

    elif len(params) > 0 and params[0] == "backlight":
        params.pop(0)
        try:
            if params[0] == "on" or params[0] == "off":
                return asyncio.run(request(ip, ['backlight', params[0]]))
            else:
                raise IndexError
        except IndexError:
            return {"ERROR": "Must specify 'on' or 'off'"}
    else:
        return {"Example usage": "./api_client.py ir [tv|ac|backlight] [command]"}


@add_endpoint("get_temp")
def get_temp(ip, params):
    return asyncio.run(request(ip, ['get_temp']))


@add_endpoint("get_humid")
def get_humid(ip, params):
    return asyncio.run(request(ip, ['get_humid']))


@add_endpoint("get_climate")
def get_climate(ip, params):
    return asyncio.run(request(ip, ['get_climate_data']))


@add_endpoint("clear_log")
def clear_log(ip, params):
    return asyncio.run(request(ip, ['clear_log']))


@add_endpoint("condition_met")
def condition_met(ip, params):
    try:
        if params[0].startswith("sensor"):
            return asyncio.run(request(ip, ['condition_met', params[0]]))
        else:
            raise IndexError
    except IndexError:
        return {"ERROR": "Must specify sensor"}


@add_endpoint("trigger_sensor")
def trigger_sensor(ip, params):
    try:
        if params[0].startswith("sensor"):
            return asyncio.run(request(ip, ['trigger_sensor', params[0]]))
        else:
            raise IndexError
    except IndexError:
        return {"ERROR": "Must specify sensor"}


@add_endpoint("turn_on")
def turn_on(ip, params):
    try:
        if params[0].startswith("device"):
            return asyncio.run(request(ip, ['turn_on', params[0]]))
        else:
            raise IndexError
    except IndexError:
        return {"ERROR": "Can only turn on/off devices, use enable/disable for sensors"}


@add_endpoint("turn_off")
def turn_off(ip, params):
    try:
        if params[0].startswith("device"):
            return asyncio.run(request(ip, ['turn_off', params[0]]))
        else:
            raise IndexError
    except IndexError:
        return {"ERROR": "Can only turn on/off devices, use enable/disable for sensors"}


if __name__ == "__main__":
    # Remove name of application from args
    sys.argv.pop(0)

    response = parse_ip(sys.argv)
    print(json.dumps(response, indent=4) + "\n")
