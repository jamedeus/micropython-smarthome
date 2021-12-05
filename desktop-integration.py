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

state = None

import os
import socket
from struct import pack
import re
import subprocess
import threading
import time



# Encrypt messages to tp-link smarthome devices
def encrypt(string):
    key = 171
    result = pack(">I", len(string))
    for i in string:
        a = key ^ ord(i)
        key = a
        result += bytes([a])
    return result



# Dencrypt messages from tp-link smarthome devices
def decrypt(string):
    key = 171
    result = ""
    for i in string:
        a = key ^ i
        key = i
        result += chr(a)
    return result



# Send set_brightness command to tp-link dimmers/smartbulbs
# dev is needed because dimmer and bulb use different syntax
def send(ip="192.168.1.233", bright=1, dev="dimmer", state=0):
    if dev == "dimmer":
        cmd = '{"smartlife.iot.dimmer":{"set_brightness":{"brightness":' + str(bright) + '}}}'
    else:
        cmd = '{"smartlife.iot.smartbulb.lightingservice":{"transition_light_state":{"ignore_default":1,"on_off":' + str(state) + ',"transition_period":0,"brightness":' + str(bright) + '}}}'

    # Send command and receive reply
    try:
        sock_tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock_tcp.settimeout(10)
        sock_tcp.connect((ip, 9999))
        #sock_tcp.settimeout(None)

        # Dimmer has seperate brightness and on/off commands, bulb combines into 1 command
        if dev == "dimmer":
            foo = encrypt('{"system":{"set_relay_state":{"state":' + str(state) + '}}}')
            sock_tcp.send(foo) # Set on/off state before brightness
            data = sock_tcp.recv(2048) # Dimmer wont listen for next command until it's reply is received

        # Set brightness
        sock_tcp.send(encrypt(cmd))
        data = sock_tcp.recv(2048)
        sock_tcp.close()

        if state:
            print("Turned overhead lights ON")
        elif not state:
            print("Turned overhead lights OFF")

        # Tell the motion sensor that lights were turned off
        s = socket.socket()
        s.connect(("192.168.1.224", 4200)) # TODO - implement config file, remove hardcoded IP
        if state:
            s.send("on".encode())
        elif not state:
            s.send("off".encode())
        s.close()

    except: # Failed
        print(f"Could not connect to host {ip}")



# Watch monitor power state, turn overhead lights off when monitors turn off
def dpms_mon():
    # Get initial state
    state = get_dpms_state()

    while True:
        # Check current state
        current = get_dpms_state()
        if not current == state:
            print(f"State changed from {state} to {current}")
            state = current
            if not "On" in current:
                send() # Turn overhead lights off when computer screen goes to sleep
            else:
                # When monitors wake up, run PRIME sync (fix cursor flicker issue)
                print("Running PRIME sync...")
                os.system('xrandr --output DisplayPort-1-4 --set "PRIME Synchronization" 1;xrandr --output DisplayPort-1-3 --set "PRIME Synchronization" 1')
        time.sleep(1)



# Query DPMS state (monitors on/off/standby etc)
def get_dpms_state():
    while True:
        current = str(subprocess.check_output('xset -q | tail -1 | cut -d " " -f 5', shell=True))[2:-3]
        if current == "Disabled": # Sometimes it's disabled for a few seconds, probably related to NVIDIA PRIME
            time.sleep(0.25) # Wait 250 ms, try again (prevent high CPU usage)
        else:
            break
    return current



# Turn monitor off, called by timer 5 seconds after lights go off
# User can prevent monitors from turning off by moving mouse OR triggering motion sensor
def off():
    global state
    if state == False: # Will be True if motion detected before timer expired
        if int(re.sub("[^0-9]", "", str(subprocess.check_output('xprintidle', shell=True)))) > 60000: # Only turn off if user has been inactive for >60 seconds
            print("Off command received, turning off")
            os.system('xset dpms force off')
        else:
            print("Off command received - user is active, keeping screen on")



# Listen for messages from esp32, allows ESP32 to turn monitors on/off to keep in sync with overhead lights
def server():
    global state

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
            current = get_dpms_state()
            # Don't turn monitor on if already on (causes artifacting)
            if not "On" in current:
                print("On command received, turning on")
                os.system('xset dpms force on')
            else:
                print("On command received, but monitors are already on")
            state = True
        elif msg == "off":
            state = False
            # Wait 5 seconds (after lights turn off) before turning monitor off, gives user a chance to override
            t = threading.Timer(interval = 5.0, function=off)
            t.start()
            print("Off command received, setting 5 sec timer")

        # Close connection, restart loop and wait for next connection
        conn.close()



thread1 = threading.Thread(target=server)
thread2 = threading.Thread(target=dpms_mon)

thread1.start()
thread2.start()
