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



def argparse():
    # Load config file
    with open('nodes.json', 'r') as file:
        nodes = json.load(file)


    # Get target ip
    for i in range(len(sys.argv)):

        if sys.argv[i] in nodes:
            ip = nodes[sys.argv[i]]["ip"]
            sys.argv.pop(i)
            break

        elif sys.argv[i] == "-ip":
            sys.argv.pop(i)
            ip = sys.argv.pop(i)
            if re.match("^[0-9]{1,3}.[0-9]{1,3}.[0-9]{1,3}.[0-9]{1,3}$", ip):
                break
            else:
                print("Error: Invalid IP format")
                exit()

        elif re.match("^[0-9]{1,3}.[0-9]{1,3}.[0-9]{1,3}.[0-9]{1,3}$", sys.argv[i]):
            ip = sys.argv.pop(i)
            break



    # Get command and args
    for i in range(len(sys.argv)):
        if sys.argv[i] == "status":
            response = asyncio.run(request(ip, ['status']))

            # Requires formatting, print here and exit before other print statement
            print(json.dumps(response, indent=4))
            exit()

        elif sys.argv[i] == "reboot":
            response = asyncio.run(request(ip, ['reboot']))

        elif sys.argv[i] == "disable":
            sys.argv.pop(i)
            if sys.argv[i].startswith("sensor") or sys.argv[i].startswith("device"):
                response = asyncio.run(request(ip, ['disable', sys.argv[i]]))
                break
            else:
                print("Error: Can only disable devices and sensors.")
                exit()

        elif sys.argv[i] == "enable":
            sys.argv.pop(i)
            if sys.argv[i].startswith("sensor") or sys.argv[i].startswith("device"):
                response = asyncio.run(request(ip, ['enable', sys.argv[i]]))
                break
            else:
                print("Error: Can only enable devices and sensors.")
                exit()

        elif sys.argv[i] == "set_rule":
            sys.argv.pop(i)
            if sys.argv[i].startswith("sensor") or sys.argv[i].startswith("device"):
                target = sys.argv.pop(i)
                try:
                    response = asyncio.run(request(ip, ['set_rule', target, sys.argv[i]]))
                    break
                except IndexError:
                    print("Error: Must speficy new rule")
                    exit()
            else:
                print("Error: Can only set rules for devices and sensors.")
                exit()

        elif sys.argv[i] == "ir":
            sys.argv.pop(i)

            if len(sys.argv) > 1 and (sys.argv[i] == "tv" or sys.argv[i] == "ac"):
                target = sys.argv.pop(i)
                try:
                    response = asyncio.run(request(ip, ['ir', target, sys.argv[i]]))
                    break
                except IndexError:
                    print("Error: Must speficy command")
                    exit()

            elif len(sys.argv) > 1 and sys.argv[i] == "backlight":
                sys.argv.pop(i)
                try:
                    if sys.argv[i] == "on" or sys.argv[i] == "off":
                        response = asyncio.run(request(ip, ['ir', 'backlight', sys.argv[i]]))
                        break
                    else:
                        raise IndexError
                except IndexError:
                    print("Error: Must specify 'on' or 'off'")
                    exit()
            else:
                print("Error: Must specify target device (tv or ac) or specify backlight [on|off]")
                exit()

        elif sys.argv[i] == "temp":
            response = asyncio.run(request(ip, ['temp']))

        elif sys.argv[i] == "humid":
            response = asyncio.run(request(ip, ['humid']))

        elif sys.argv[i] == "clear_log":
            response = asyncio.run(request(ip, ['clear_log']))



    try:
        # Print response, if any
        if response == "OK":
            exit()
        else:
            print(response)
    except UnboundLocalError:
        error()



argparse()
