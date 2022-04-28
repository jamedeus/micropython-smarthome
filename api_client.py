#!/usr/bin/python3

import os
import sys
from colorama import Fore, Style
import json
import asyncio
import re

def error():
    print()
    print(Fore.RED + "Error: please pass one of the following commands as argument:" + Fore.RESET + "\n")
    print("- " + Fore.YELLOW + Style.BRIGHT + "status" + Style.RESET_ALL + "                            Get dict containing status of the node (including names of sensors)")
    print("- " + Fore.YELLOW + Style.BRIGHT + "disable [target]" + Style.RESET_ALL + "                  Disable [target], can be device or sensor")
    print("- " + Fore.YELLOW + Style.BRIGHT + "disable_in [target] [minutes]" + Style.RESET_ALL + "     Create timer to disable [target] in [minutes]")
    print("- " + Fore.YELLOW + Style.BRIGHT + "enable [target]" + Style.RESET_ALL + "                   Enable [target], can be device or sensor")
    print("- " + Fore.YELLOW + Style.BRIGHT + "enable_in [target] [minutes]" + Style.RESET_ALL + "      Create timer to enable [target] in [minutes]")
    print("- " + Fore.YELLOW + Style.BRIGHT + "set_rule [target]" + Style.RESET_ALL + "                 Change [target]'s current rule, can be device or sensor, lasts until next rule change")
    print("- " + Fore.YELLOW + Style.BRIGHT + "reset_rule [target]" + Style.RESET_ALL + "               Replace [target]'s current rule with scheduled rule, used to undo a set_rule request")
    print("- " + Fore.YELLOW + Style.BRIGHT + "get_schedule_rules [target]" + Style.RESET_ALL + "       View scheduled rule changes for [target], can be device or sensor")
    print("- " + Fore.YELLOW + Style.BRIGHT + "add_rule [target] [HH:MM] [rule]" + Style.RESET_ALL + "  Add scheduled rule change, will persist until next reboot")
    print("- " + Fore.YELLOW + Style.BRIGHT + "get_attributes [target]" + Style.RESET_ALL + "           View all of [target]'s attributes, can be device or sensor")
    print("- " + Fore.YELLOW + Style.BRIGHT + "condition_met [sensor]" + Style.RESET_ALL + "            Check if [sensor]'s condition is met (turns on target devices)")
    print("- " + Fore.YELLOW + Style.BRIGHT + "trigger_sensor [sensor]" + Style.RESET_ALL + "           Simulates the sensor being triggered (turns on target devices)")
    print("- " + Fore.YELLOW + Style.BRIGHT + "turn_on [device]" + Style.RESET_ALL + "                  Turn the device on (note: loop may undo this in some situations, disable sensor to prevent)")
    print("- " + Fore.YELLOW + Style.BRIGHT + "turn_off [device]" + Style.RESET_ALL + "                 Turn the device off (note: loop may undo this in some situations, disable sensor to prevent)")
    print("- " + Fore.YELLOW + Style.BRIGHT + "ir [target||key]" + Style.RESET_ALL + "                  Simulate 'key' being pressed on remote control for 'target' (target can be tv or ac)")
    print("- " + Fore.YELLOW + Style.BRIGHT + "get_temp" + Style.RESET_ALL + "                          Get current reading from temp sensor in Farenheit")
    print("- " + Fore.YELLOW + Style.BRIGHT + "get_humid" + Style.RESET_ALL + "                         Get current relative humidity from temp sensor")
    print("- " + Fore.YELLOW + Style.BRIGHT + "clear_log" + Style.RESET_ALL + "                         Delete node's log file\n")
    exit()



async def request(ip, msg):
    reader, writer = await asyncio.open_connection(ip, 8123)
    try:
        writer.write('{}\n'.format(json.dumps(msg)).encode())
        await writer.drain()
        res = await reader.read(1000)
    except OSError:
        return "Error: Request failed"
    try:
        response = json.loads(res)
    except ValueError:
        return "Error: Unable to decode response"
    writer.close()
    await writer.wait_closed()

    return response



def parse_ip():
    # Load config file
    with open('nodes.json', 'r') as file:
        nodes = json.load(file)

    # Remove name of application from args
    sys.argv.pop(0)

    # Get target ip
    for i in range(len(sys.argv)):

        if sys.argv[i] == "--all":
            sys.argv.pop(i)
            for i in nodes:
                ip = nodes[i]["ip"]
                print(ip)
                # Use copy of original args since items are removed by parser
                cmd = sys.argv.copy()
                parse_command(ip, cmd)
            exit()

        elif sys.argv[i] in nodes:
            ip = nodes[sys.argv[i]]["ip"]
            sys.argv.pop(i)
            parse_command(ip, sys.argv)
            exit()

        elif sys.argv[i] == "-ip":
            sys.argv.pop(i)
            ip = sys.argv.pop(i)
            if re.match("^[0-9]{1,3}.[0-9]{1,3}.[0-9]{1,3}.[0-9]{1,3}$", ip):
                parse_command(ip, sys.argv)
                exit()
            else:
                print("Error: Invalid IP format")
                exit()

        elif re.match("^[0-9]{1,3}.[0-9]{1,3}.[0-9]{1,3}.[0-9]{1,3}$", sys.argv[i]):
            ip = sys.argv.pop(i)
            parse_command(ip, sys.argv)
            exit()

    else:
        print(Fore.RED + "Error: Must specify target ip, or one of the following names:" + Fore.RESET)
        for name in nodes:
            print(f" - {name}")



def parse_command(ip, args):
    if len(args) == 0:
        error()

    for endpoint in endpoints:
        if args[0] == endpoint[0]:
            # Remove endpoint arg
            args.pop(0)
            # Send remaining args to handler function
            response = endpoint[1](ip, args)
            break

    else:
        error()

    print(json.dumps(response, indent=4) + "\n")
    exit()



# Populated with endpoint:handler pairs by decorators below
endpoints = []

def add_endpoint(url):
    def _add_endpoint(func):
        endpoints.append((url, func))
        return func
    return _add_endpoint

@add_endpoint("status")
def status(ip, params):
    response = asyncio.run(request(ip, ['status']))
    return response

@add_endpoint("reboot")
def reboot(ip, params):
    response = asyncio.run(request(ip, ['reboot']))
    return response

@add_endpoint("disable")
def disable(ip, params):
    if params[0].startswith("sensor") or params[0].startswith("device"):
        response = asyncio.run(request(ip, ['disable', params[0]]))
    else:
        response = {"ERROR" : "Can only disable devices and sensors."}
    return response

@add_endpoint("disable_in")
def disable_in(ip, params):
    if params[0].startswith("sensor") or params[0].startswith("device"):
        target = params.pop(0)
        try:
            period = float(params[0])
            response = asyncio.run(request(ip, ['disable_in', target, period]))
        except ValueError:
            response = {"ERROR": "Please specify delay in minutes"}
    else:
        response = {"ERROR": "Can only disable devices and sensors"}

    return response

@add_endpoint("enable")
def disable(ip, params):
    if params[0].startswith("sensor") or params[0].startswith("device"):
        response = asyncio.run(request(ip, ['enable', params[0]]))
    else:
        response = {"ERROR" : "Can only disable devices and sensors."}
    return response

@add_endpoint("enable_in")
def enable_in(ip, params):
    if params[0].startswith("sensor") or params[0].startswith("device"):
        target = params.pop(0)
        try:
            period = float(params[0])
            response = asyncio.run(request(ip, ['enable_in', target, period]))
        except ValueError:
            response = {"ERROR": "Please specify delay in minutes"}
    else:
        response = {"ERROR": "Can only enable devices and sensors"}

    return response

@add_endpoint("set_rule")
def set_rule(ip, params):
    if params[0].startswith("sensor") or params[0].startswith("device"):
        target = params.pop(0)
        try:
            response = asyncio.run(request(ip, ['set_rule', target, params[0]]))
        except IndexError:
            response = {"ERROR": "Must specify new rule"}
    else:
        response = {"ERROR": "Can only set rules for devices and sensors"}

    return response

@add_endpoint("reset_rule")
def reset_rule(ip, params):
    if params[0].startswith("sensor") or params[0].startswith("device"):
        target = params.pop(0)
        response = asyncio.run(request(ip, ['reset_rule', target]))
    else:
        response = {"ERROR": "Can only set rules for devices and sensors"}

    return response

@add_endpoint("get_schedule_rules")
def get_schedule_rules(ip, params):
    if params[0].startswith("sensor") or params[0].startswith("device"):
        target = params.pop(0)
        response = asyncio.run(request(ip, ['get_schedule_rules', target]))
    else:
        response = {"ERROR": "Only devices and sensors have schedule rules"}

    return response

@add_endpoint("add_rule")
def add_schedule_rule(ip, params):
    if params[0].startswith("sensor") or params[0].startswith("device"):
        target = params.pop(0)

        try:
            response = asyncio.run(request(ip, ['add_schedule_rule', target, params[0], params[1]]))
        except IndexError:
            response = {"ERROR": "Must specify time (HH:MM) followed by rule"}

    else:
        response = {"ERROR": "Only devices and sensors have schedule rules"}

    return response

@add_endpoint("get_attributes")
def get_attributes(ip, params):
    if params[0].startswith("sensor") or params[0].startswith("device"):
        target = params.pop(0)
        response = asyncio.run(request(ip, ['get_attributes', target]))
    else:
        response = {"ERROR": "Must specify device or sensor"}

    return response

@add_endpoint("ir")
def ir(ip, params):
    if len(params) > 1 and (params[0] == "tv" or params[0] == "ac"):
        target = params.pop(0)
        try:
            response = asyncio.run(request(ip, ['ir_key', target, params[0]]))
        except IndexError:
            response = {"ERROR": "Must specify command"}

    elif len(params) > 1 and params[0] == "backlight":
        params.pop(0)
        try:
            if params[0] == "on" or params[0] == "off":
                response = asyncio.run(request(ip, ['backlight', params[0]]))
            else:
                raise IndexError
        except IndexError:
            response = {"ERROR": "Must specify 'on' or 'off'"}
    else:
        response = {"ERROR": "Must specify target device (tv or ac) or specify backlight [on|off]"}

    return response

@add_endpoint("get_temp")
def get_temp(ip, params):
    response = asyncio.run(request(ip, ['get_temp']))
    return response

@add_endpoint("get_humid")
def get_humid(ip, params):
    response = asyncio.run(request(ip, ['get_humid']))
    return response

@add_endpoint("clear_log")
def clear_log(ip, params):
    response = asyncio.run(request(ip, ['clear_log']))
    return response

@add_endpoint("condition_met")
def condition_met(ip, params):
    try:
        if params[0].startswith("sensor"):
            response = asyncio.run(request(ip, ['condition_met', params[0]]))
        else:
            raise IndexError
    except IndexError:
        response = {"ERROR": "Must specify sensor"}

    return response

@add_endpoint("trigger_sensor")
def trigger_sensor(ip, params):
    try:
        if params[0].startswith("sensor"):
            response = asyncio.run(request(ip, ['trigger_sensor', params[0]]))
        else:
            raise IndexError
    except IndexError:
        response = {"ERROR": "Must specify sensor"}

    return response

@add_endpoint("turn_on")
def turn_on(ip, params):
    try:
        if params[0].startswith("device"):
            response = asyncio.run(request(ip, ['turn_on', params[0]]))
        else:
            raise IndexError
    except IndexError:
        response = {"ERROR": "Can only turn on/off devices, use enable/disable for sensors"}

    return response

@add_endpoint("turn_off")
def turn_on(ip, params):
    try:
        if params[0].startswith("device"):
            response = asyncio.run(request(ip, ['turn_off', params[0]]))
        else:
            raise IndexError
    except IndexError:
        response = {"ERROR": "Can only turn on/off devices, use enable/disable for sensors"}

    return response



parse_ip()
