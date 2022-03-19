#!/usr/bin/python3

import os
import sys
from colorama import Fore, Style
import socket
import subprocess
import threading # TODO remove
import time
import json
import asyncio
import re

functions = ("status", "reboot", "enable", "disable", "set_rule", "ir", "temp", "humid", "clear_log")

def error():
    print()
    print(Fore.RED + "Error: please pass one of the following commands as argument:" + Fore.RESET + "\n")
    print("- " + Fore.YELLOW + Style.BRIGHT + "status" + Style.RESET_ALL + "                         Get dict containing status of the node (including names of sensors)")
    print("- " + Fore.YELLOW + Style.BRIGHT + "disable [sensor] [minutes]" + Style.RESET_ALL + "     Disable [sensor], keeps lights in current state. Optionally schedule to re-enable in [minutes]")
    print("- " + Fore.YELLOW + Style.BRIGHT + "enable [sensor]" + Style.RESET_ALL + "                Enable [sensor], allows it to turn lights on/off again")
    print("- " + Fore.YELLOW + Style.BRIGHT + "set_rule [sensor||device]" + Style.RESET_ALL + "      Change current rule (brightness for dev, delay for sensor). Lasts until next rule change.")
    print("- " + Fore.YELLOW + Style.BRIGHT + "ir [target||key]" + Style.RESET_ALL + "               Simulate 'key' being pressed on remote control for 'target' (target can be tv or ac).")
    print("- " + Fore.YELLOW + Style.BRIGHT + "temp" + Style.RESET_ALL + "                           Get current reading from temp sensor in Farenheit.")
    print("- " + Fore.YELLOW + Style.BRIGHT + "humid" + Style.RESET_ALL + "                          Get current relative humidity from temp sensor.")
    print("- " + Fore.YELLOW + Style.BRIGHT + "clear_log" + Style.RESET_ALL + "                      Delete node's log file.\n")
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

        elif args[i] == "enable":
            args.pop(i)
            if args[i].startswith("sensor") or args[i].startswith("device"):
                response = asyncio.run(request(ip, ['enable', args[i]]))
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

        elif args[i] == "temp":
            response = asyncio.run(request(ip, ['temp']))

        elif args[i] == "humid":
            response = asyncio.run(request(ip, ['humid']))

        elif args[i] == "clear_log":
            response = asyncio.run(request(ip, ['clear_log']))



    try:
        # Print response, if any
        if response == "OK":
            return True
        else:
            print(response)
    except UnboundLocalError:
        error()



parse_ip()
