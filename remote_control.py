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

functions = ("status", "reboot", "enable", "disable", "set_rule")

def error():
    print()
    print(Fore.RED + "Error: please pass one of the following commands as argument:" + Fore.RESET + "\n")
    print("- " + Fore.YELLOW + Style.BRIGHT + "status" + Style.RESET_ALL + "                         Get dict containing status of the node (including names of sensors)")
    print("- " + Fore.YELLOW + Style.BRIGHT + "disable [sensor] [minutes]" + Style.RESET_ALL + "     Disable [sensor], keeps lights in current state. Optionally schedule to re-enable in [minutes]")
    print("- " + Fore.YELLOW + Style.BRIGHT + "enable [sensor]" + Style.RESET_ALL + "                Enable [sensor], allows it to turn lights on/off again")
    print("- " + Fore.YELLOW + Style.BRIGHT + "set_rule [sensor||device]" + Style.RESET_ALL + "      Change current rule (brightness for dev, delay for sensor). Lasts until next rule change.\n")
    exit()



async def request(msg):
    reader, writer = await asyncio.open_connection('192.168.1.224', 8123)
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



# Input validation
try:
    if not sys.argv[1] in functions:
        error()
except IndexError:
    error()

# Parse argument, call request function with appropriate params
if sys.argv[1] == "status":
    response = asyncio.run(request(['status']))

    # Requires formatting, print here and exit before other print statement
    print(json.dumps(response, indent=4))
    exit()

elif sys.argv[1] == "reboot":
    response = asyncio.run(request(['reboot']))

elif len(sys.argv) > 2 and sys.argv[1] == "disable" and sys.argv[2].startswith("sensor"):
    response = asyncio.run(request(['disable', sys.argv[2]]))
    if len(sys.argv) > 3:
        if sys.argv[3].isdecimal():
            t = threading.Timer(int(sys.argv[3])*60, lambda: asyncio.run(request(['enable', sys.argv[2]])))
            t.start()
        else:
            print(Fore.RED + "Error: 3rd argument must either be blank or contain number of minutes to disable sensor" + Fore.RESET + "\n")

elif len(sys.argv) > 2 and sys.argv[1] == "enable" and sys.argv[2].startswith("sensor"):
    response = asyncio.run(request(['enable', sys.argv[2]]))

elif len(sys.argv) > 3 and sys.argv[1] == "set_rule" and (sys.argv[2].startswith("sensor") or sys.argv[2].startswith("device")):
    response = asyncio.run(request(['set_rule', sys.argv[2], sys.argv[3]]))

else:
    response = "Error: Invalid argument"

if response == "OK":
    exit()
else:
    print(response)
