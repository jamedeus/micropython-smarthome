#!/usr/bin/python3

# Note: This is NOT a micropython script, it is a regular CPython script
# Allows computer to turn monitor on/off when bedroom lights turn on/off
#
# ESP that detects motion must run pir-tplink.py
# config.json must contain a device entry for computer running this code
# - ip = computer's IP
# - type = "relay"
# - schedule rule values are "on" and "off"
#
# Install in ~/.config/autorun-scripts

import os
import socket
import re
import subprocess
from threading import Timer

state = None

# Turn monitor off, called by timer 5 seconds after lights go off
# Gives user a chance to trigger motion sensor and prevent monitor turning off
def off():
    if state == False: # Will be True if motion detected before timer expired
        if int(re.sub("[^0-9]", "", str(subprocess.check_output('xprintidle', shell=True)))) > 60000: # Only turn off if user has been inactive for >60 seconds
            print("Timer expired, turning off")
            os.system('xset dpms force off')
        else:
            print("Timer expired, but user is active - keeping screen on")



# Create socket listening on port 4200
s = socket.socket()
s.bind(('', 4200))
s.listen(1)

# Handle connections
while True:
    # Accept connection, decode message
    conn, addr = s.accept()
    msg = conn.recv(8).decode()

    if msg == "on":
        # Check if monitor is currently on or off
        with open('/sys/devices/pci0000:00/0000:00:01.0/0000:01:00.0/drm/card1/card1-DP-4/dpms', 'r') as file:
            current = file.read()
        # Only turn on if it's currently off (turning on when already on causes artifacting)
        if "Off" in current:
            print("On command received, turning on")
            os.system('xset dpms force on')
            os.system('xrandr --output DisplayPort-1-4 --set "PRIME Synchronization" 1;xrandr --output DisplayPort-1-3 --set "PRIME Synchronization" 1')
        else:
            print("On command received, but monitors are already on")
        state = True
    elif msg == "off":
        # Wait 5 seconds (after lights turn off) before turning monitor off
        state = False
        t = Timer(interval = 5.0, function=off)
        t.start()
        print("Off command received, setting 5 sec timer")

    # Close connection, restart loop and wait for next connection
    conn.close()
