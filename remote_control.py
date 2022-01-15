#!/usr/bin/python3

import os
import sys
from colorama import Fore, Style
import socket
import subprocess
import threading
import time
import json

functions = ("status", "enable", "disable")

def error():
    print()
    print(Fore.RED + "Error: please pass one of the following commands as argument:" + Fore.RESET + "\n")
    print("- " + Fore.YELLOW + Style.BRIGHT + "status" + Style.RESET_ALL + "                         Get dict containing status of the node (including names of sensors)")
    print("- " + Fore.YELLOW + Style.BRIGHT + "disable [sensor] [minutes]" + Style.RESET_ALL + "     Disable [sensor], keeps lights in current state. Optionally schedule to re-enable in [minutes]")
    print("- " + Fore.YELLOW + Style.BRIGHT + "enable [sensor]" + Style.RESET_ALL + "                Enable [sensor], allows it to turn lights on/off again\n")
    exit()



def request(arg):
    s = socket.socket()
    s.connect(('192.168.1.224', 6969))
    s.send(json.dumps(arg).encode())
    data = s.recv(4096)
    return json.loads(data)



# Input validation
try:
    if not sys.argv[1] in functions:
        error()
except IndexError:
    error()



# Parse argument, call request function with appropriate params
if sys.argv[1] == "status":
    data = request("status")
    print(json.dumps(data, indent=4))
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
