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
from threading import Timer

state = None

os.system('export DISPLAY=":0"')

# Turn monitor off, called by timer 5 seconds after lights go off
# Gives user a chance to trigger motion sensor and prevent monitor turning off
def off():
    if state == False: # Will be True if motion detected before timer expired
        os.system('xset dpms force off')



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
        # Turn monitor on immediately when motion detected
        os.system('xset dpms force on')
        os.system('xrandr --output DisplayPort-1-4 --set "PRIME Synchronization" 1;xrandr --output DisplayPort-1-3 --set "PRIME Synchronization" 1')
        state = True
    elif msg == "off":
        # Wait 5 seconds (after lights turn off) before turning monitor off
        state = False
        t = Timer(interval = 5.0, function=off)
        t.start()

    # Close connection, restart loop and wait for next connection
    conn.close()
