#!/usr/bin/python3

import os
import sys
from colorama import Fore, Style
import socket
import subprocess
import threading
import time
import json

functions = ("status", "reboot", "enable", "disable", "set_rule")

def error():
    print()
    print(Fore.RED + "Error: please pass one of the following commands as argument:" + Fore.RESET + "\n")
    print("- " + Fore.YELLOW + Style.BRIGHT + "status" + Style.RESET_ALL + "                         Get dict containing status of the node (including names of sensors)")
    print("- " + Fore.YELLOW + Style.BRIGHT + "disable [sensor] [minutes]" + Style.RESET_ALL + "     Disable [sensor], keeps lights in current state. Optionally schedule to re-enable in [minutes]")
    print("- " + Fore.YELLOW + Style.BRIGHT + "enable [sensor]" + Style.RESET_ALL + "                Enable [sensor], allows it to turn lights on/off again")
    print("- " + Fore.YELLOW + Style.BRIGHT + "set_rule [sensor||device]" + Style.RESET_ALL + "      Change current rule (brightness for dev, delay for sensor). Lasts until next rule change.\n")
    exit()



def request(arg):
    try:
        s = socket.socket()
        s.settimeout(10)
        s.connect(('192.168.1.224', 6969))
        s.send(json.dumps(arg).encode())
        # TODO: Figure out how to receive data (below doesn't work), may need to use asyncio on both sides?
        #data = s.recv(4096)
        #return data
        #if json.loads(data) == "done":
            #print("Success")
        #else:
            #print("Invalid input, command failed")
    except socket.timeout:
        print("Timed out while connecting to node")



# Input validation
try:
    if not sys.argv[1] in functions:
        error()
except IndexError:
    error()



# Parse argument, call request function with appropriate params
if sys.argv[1] == "status":
    print("Status command under construction, exiting")
    exit()
    #data = request("status")
    #print(json.dumps(data, indent=4))

elif sys.argv[1] == "reboot":
    request(['reboot'])
elif sys.argv[1] == "disable" and sys.argv[2].startswith("sensor"):
    request(['disable', sys.argv[2]])
    if len(sys.argv) > 3:
        if sys.argv[3].isdecimal():
            t = threading.Timer(int(sys.argv[3])*60, lambda: request(['enable', sys.argv[2]]))
            t.start()
        else:
            print(Fore.RED + "Error: 3rd argument must either be blank or contain number of minutes to disable sensor" + Fore.RESET + "\n")

elif sys.argv[1] == "enable" and sys.argv[2].startswith("sensor"):
    request(['enable', sys.argv[2]])

elif sys.argv[1] == "set_rule" and sys.argv[2].startswith("sensor") or sys.argv[2].startswith("device") and sys.argv[3]:
    request(['set_rule', sys.argv[2], sys.argv[3]])
