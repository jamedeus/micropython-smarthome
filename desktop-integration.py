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



class Tplink():
    def __init__(self, ip="192.168.1.233", device="dimmer", bright=1):
        self.ip = ip
        self.device = device
        self.bright = bright



    def encrypt(self, string):
        key = 171
        result = pack(">I", len(string))
        for i in string:
            a = key ^ ord(i)
            key = a
            result += bytes([a])
        return result



    def decrypt(self, string):
        key = 171
        result = ""
        for i in string:
            a = key ^ i
            key = i
            result += chr(a)
        return result



    # Send set_brightness command to tp-link dimmers/smartbulbs (dev type needed, dimmer and bulb use different syntax)
    def send(self, state=0):
        if self.device == "dimmer":
            cmd = '{"smartlife.iot.dimmer":{"set_brightness":{"brightness":' + str(self.bright) + '}}}'
        else:
            cmd = '{"smartlife.iot.smartbulb.lightingservice":{"transition_light_state":{"ignore_default":1,"on_off":' + str(state) + ',"transition_period":0,"brightness":' + str(self.bright) + '}}}'

        # Send command and receive reply
        try:
            sock_tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock_tcp.settimeout(10)
            sock_tcp.connect((self.ip, 9999))
            #sock_tcp.settimeout(None)

            # Dimmer has seperate brightness and on/off commands, bulb combines into 1 command
            if self.device == "dimmer":
                foo = self.encrypt('{"system":{"set_relay_state":{"state":' + str(state) + '}}}')
                sock_tcp.send(foo) # Set on/off state before brightness
                data = sock_tcp.recv(2048) # Dimmer wont listen for next command until it's reply is received

            # Set brightness
            sock_tcp.send(self.encrypt(cmd))
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
            print(f"Could not connect to host {self.ip}")



class Desktop():
    # Watch monitor power state, turn overhead lights off when monitors turn off
    def dpms_mon(self):
        # Create target instance
        lights = Tplink()

        # Get initial monitor state (on/offstandby etc)
        dpms_state = self.get_dpms_state()

        while True:
            # Check current state
            current = self.get_dpms_state()
            if not current == dpms_state:
                print(f"Monitors changed from {dpms_state} to {current}")
                dpms_state = current
                if not "On" in current:
                    lights.send() # Turn overhead lights off when computer screen goes to sleep
                else:
                    # When monitors wake up, run PRIME sync (fix cursor flicker issue)
                    print("Running PRIME sync...")
                    os.system('xrandr --output DisplayPort-1-4 --set "PRIME Synchronization" 1;xrandr --output DisplayPort-1-3 --set "PRIME Synchronization" 1')
            time.sleep(1)



    # Query DPMS state (monitors on/off/standby etc)
    def get_dpms_state(self):
        while True:
            current = str(subprocess.check_output('xset -q | tail -1 | cut -d " " -f 5', shell=True))[2:-3]
            if current == "Disabled": # Sometimes it's disabled for a few seconds, probably related to NVIDIA PRIME
                time.sleep(0.25) # Wait 250 ms, try again (prevent high CPU usage)
            else:
                break
        return current



    # Turn monitor off, called by timer 5 seconds after lights go off
    # User can prevent monitors from turning off by moving mouse OR triggering motion sensor
    def off(self):
        if self.state == False: # Will be True if motion detected before timer expired
            if int(re.sub("[^0-9]", "", str(subprocess.check_output('xprintidle', shell=True)))) > 60000: # Only turn off if user has been inactive for >60 seconds
                print("Off command received from motion sensor, turning screen off")
                os.system('xset dpms force off')
            else:
                print("Off command received - user is active, keeping screen on")



    # Listen for messages from esp32, allows ESP32 to turn monitors on/off to keep in sync with overhead lights
    def server(self):
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
                current = self.get_dpms_state() # TODO - just use the class attribute? Could be up to 1 second out of date, consider consequences
                # Don't turn monitor on if already on (causes artifacting)
                if not "On" in current:
                    print("On command received from motion sensor, turning screen on")
                    os.system('xset dpms force on')
                else:
                    print("On command received, but monitors are already on")
                self.state = True
            elif msg == "off":
                self.state = False
                # Wait 5 seconds (after lights turn off) before turning monitor off, gives user a chance to override
                t = threading.Timer(interval = 5.0, function=self.off)
                t.start()
                print("Off command received from motion sensor, setting 5 sec timer")

            # Close connection, restart loop and wait for next connection
            conn.close()



desktop = Desktop()

thread1 = threading.Thread(target=desktop.server)
thread2 = threading.Thread(target=desktop.dpms_mon)

# NOTE: Order is important! If thread1 started first it will block thread2 from starting until server receives first request
# Can confirm by adding print line in dpms_mon loop. This did not happen before rewriting with classes
# Should probably port this to asyncio anyway
thread2.start()
thread1.start()
