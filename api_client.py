#!/usr/bin/python3

import os
import sys
from colorama import Fore, Style
import json
import asyncio
import re

functions = ("status", "reboot", "enable", "enable_in", "disable", "disable_in", "set_rule", "reset_rule", "get_schedule_rules", "condition_met", "trigger_sensor", "turn_on", "turn_off", "ir", "get_temp", "get_humid", "clear_log")

def error():
    print()
    print(Fore.RED + "Error: please pass one of the following commands as argument:" + Fore.RESET + "\n")
    print("- " + Fore.YELLOW + Style.BRIGHT + "status" + Style.RESET_ALL + "                         Get dict containing status of the node (including names of sensors)")
    print("- " + Fore.YELLOW + Style.BRIGHT + "disable [target]" + Style.RESET_ALL + "               Disable [target], can be device or sensor")
    print("- " + Fore.YELLOW + Style.BRIGHT + "disable_in [target] [minutes]" + Style.RESET_ALL + "  Create timer to disable [target] in [minutes]")
    print("- " + Fore.YELLOW + Style.BRIGHT + "enable [target]" + Style.RESET_ALL + "                Enable [target], can be device or sensor")
    print("- " + Fore.YELLOW + Style.BRIGHT + "enable_in [target] [minutes]" + Style.RESET_ALL + "   Create timer to enable [target] in [minutes]")
    print("- " + Fore.YELLOW + Style.BRIGHT + "set_rule [target]" + Style.RESET_ALL + "              Change [target]'s current rule, can be device or sensor, lasts until next rule change")
    print("- " + Fore.YELLOW + Style.BRIGHT + "reset_rule [target]" + Style.RESET_ALL + "            Replace [target]'s current rule with scheduled rule, used to undo a set_rule request")
    print("- " + Fore.YELLOW + Style.BRIGHT + "get_schedule_rules [target]" + Style.RESET_ALL + "    View scheduled rule changes for [target], can be device or sensor")
    print("- " + Fore.YELLOW + Style.BRIGHT + "condition_met [sensor]" + Style.RESET_ALL + "         Check if [sensor]'s condition is met (turns on target devices)")
    print("- " + Fore.YELLOW + Style.BRIGHT + "trigger_sensor [sensor]" + Style.RESET_ALL + "        Simulates the sensor being triggered (turns on target devices)")
    print("- " + Fore.YELLOW + Style.BRIGHT + "turn_on [device]" + Style.RESET_ALL + "               Turn the device on (note: loop may undo this in some situations, disable sensor to prevent)")
    print("- " + Fore.YELLOW + Style.BRIGHT + "turn_off [device]" + Style.RESET_ALL + "              Turn the device off (note: loop may undo this in some situations, disable sensor to prevent)")
    print("- " + Fore.YELLOW + Style.BRIGHT + "ir [target||key]" + Style.RESET_ALL + "               Simulate 'key' being pressed on remote control for 'target' (target can be tv or ac)")
    print("- " + Fore.YELLOW + Style.BRIGHT + "get_temp" + Style.RESET_ALL + "                       Get current reading from temp sensor in Farenheit")
    print("- " + Fore.YELLOW + Style.BRIGHT + "get_humid" + Style.RESET_ALL + "                      Get current relative humidity from temp sensor")
    print("- " + Fore.YELLOW + Style.BRIGHT + "clear_log" + Style.RESET_ALL + "                      Delete node's log file\n")
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



def parse_command(ip, args):
    # Get command and args
    for i in range(len(sys.argv)):
        if args[i] == "status":
            response = asyncio.run(request(ip, ['status']))

            # Requires formatting, print here and exit before other print statement
            print(json.dumps(response, indent=4) + "\n")
            return True

        elif args[i] == "reboot":
            response = asyncio.run(request(ip, ['reboot']))

        elif args[i] == "disable":
            args.pop(i)
            if args[i].startswith("sensor") or args[i].startswith("device"):
                response = asyncio.run(request(ip, ['disable', args[i]]))
                break
            else:
                print("Error: Can only disable devices and sensors.")
                exit()

        elif args[i] == "disable_in":
            args.pop(i)
            if args[i].startswith("sensor") or args[i].startswith("device"):
                target = args.pop(i)
                try:
                    period = float(args[i])
                    response = asyncio.run(request(ip, ['disable_in', target, period]))
                except ValueError:
                    print("Error: Please specify delay in minutes")
                    exit()
                break
            else:
                print("Error: Can only disable devices and sensors.")
                exit()

        elif args[i] == "enable":
            args.pop(i)
            if args[i].startswith("sensor") or args[i].startswith("device"):
                response = asyncio.run(request(ip, ['enable', args[i]]))
                break
            else:
                print("Error: Can only enable devices and sensors.")
                exit()

        elif args[i] == "enable_in":
            args.pop(i)
            if args[i].startswith("sensor") or args[i].startswith("device"):
                target = args.pop(i)
                try:
                    period = float(args[i])
                    response = asyncio.run(request(ip, ['enable_in', target, period]))
                except ValueError:
                    print("Error: Please specify delay in minutes")
                    exit()
                break
            else:
                print("Error: Can only enable devices and sensors.")
                exit()

        elif args[i] == "set_rule":
            args.pop(i)
            if args[i].startswith("sensor") or args[i].startswith("device"):
                target = args.pop(i)
                try:
                    response = asyncio.run(request(ip, ['set_rule', target, args[i]]))
                    break
                except IndexError:
                    print("Error: Must speficy new rule")
                    exit()
            else:
                print("Error: Can only set rules for devices and sensors.")
                exit()

        elif args[i] == "reset_rule":
            args.pop(i)
            if args[i].startswith("sensor") or args[i].startswith("device"):
                target = args.pop(i)
                response = asyncio.run(request(ip, ['reset_rule', target]))
                break

            else:
                print("Error: Can only reset rules for devices and sensors.")
                exit()

        elif args[i] == "get_schedule_rules":
            args.pop(i)
            if args[i].startswith("sensor") or args[i].startswith("device"):
                target = args.pop(i)
                response = asyncio.run(request(ip, ['get_schedule_rules', target]))

                # Requires formatting, print here and exit before other print statement
                print(json.dumps(response, indent=4) + "\n")
                return True

            else:
                print("Error: Only devices and sensors have schedule rules.")
                exit()

        elif args[i] == "ir":
            args.pop(i)

            if len(sys.argv) > 1 and (args[i] == "tv" or args[i] == "ac"):
                target = args.pop(i)
                try:
                    response = asyncio.run(request(ip, ['ir', target, args[i]]))
                    break
                except IndexError:
                    print("Error: Must speficy command")
                    exit()

            elif len(sys.argv) > 1 and args[i] == "backlight":
                args.pop(i)
                try:
                    if args[i] == "on" or args[i] == "off":
                        response = asyncio.run(request(ip, ['ir', 'backlight', args[i]]))
                        break
                    else:
                        raise IndexError
                except IndexError:
                    print("Error: Must specify 'on' or 'off'")
                    exit()
            else:
                print("Error: Must specify target device (tv or ac) or specify backlight [on|off]")
                exit()

        elif args[i] == "get_temp":
            response = asyncio.run(request(ip, ['get_temp']))

        elif args[i] == "get_humid":
            response = asyncio.run(request(ip, ['get_humid']))

        elif args[i] == "clear_log":
            response = asyncio.run(request(ip, ['clear_log']))

        elif args[i] == "condition_met":
            args.pop(i)
            if args[i].startswith("sensor"):
                target = args.pop(i)
                response = asyncio.run(request(ip, ['condition_met', target]))
                break

        elif args[i] == "trigger_sensor":
            args.pop(i)
            if args[i].startswith("sensor"):
                target = args.pop(i)
                response = asyncio.run(request(ip, ['trigger_sensor', target]))
                break

        elif args[i] == "turn_on":
            args.pop(i)
            if args[i].startswith("device"):
                target = args.pop(i)
                response = asyncio.run(request(ip, ['turn_on', target]))
                break
            else:
                print("Error: Can only turn on/off devices, use enable/disable for sensors.")
                exit()

        elif args[i] == "turn_off":
            args.pop(i)
            if args[i].startswith("device"):
                target = args.pop(i)
                response = asyncio.run(request(ip, ['turn_off', target]))
                break
            else:
                print("Error: Can only turn on/off devices, use enable/disable for sensors.")
                exit()

    try:
        # Print response, if any
        if response == "OK":
            return True
        else:
            print(response)
    except UnboundLocalError:
        error()



parse_ip()
