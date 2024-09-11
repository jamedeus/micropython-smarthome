#!/usr/bin/python3

import re
import os
import time
import threading
import subprocess
from flask import Flask

app = Flask(__name__)


# Returns current DPMS state (On, Off, Standby, Disabled)
@app.get("/state")
def get_dpms_state():
    try:
        current = subprocess.check_output('xset -q | tail -1 | cut -d " " -f 5', shell=True, stderr=subprocess.STDOUT)
        current = str(current)[2:-3]
        return {'state': current}, 200
    except Exception as ex:
        return {'Error': ex}, 500


# Returns milliseconds since last keyboard/mouse input
@app.get("/idle_time")
def get_idle_time():
    try:
        idle = re.sub("[^0-9]", "", str(subprocess.check_output('xprintidle', shell=True)))
        return {'idle_time': idle}, 200
    except Exception as ex:
        return {'Error': ex}, 500


# Turns screen on
@app.get("/on")
def monitor_on():
    try:
        os.system('xset dpms force on')
        return {'state': 'on'}, 200
    except Exception as ex:
        return {'Error': ex}, 500


# Turns screen off after 5 second delay if user is idle
@app.get("/off")
def monitor_off():
    try:
        # Only turn off if no user activity in last 60 seconds
        if user_is_idle():
            # Start 5 second countdown, turn off screen if user still idle
            # Gives user a chance to move mouse and keep screen on
            thread = threading.Thread(target=turn_off_after_delay)
            thread.start()
            return {'state': 'off'}, 200
        else:
            return {'state': 'user not idle'}, 503
    except Exception as ex:
        return {'Error': ex}, 500


# Returns True if no mouse/keyboard activity in last 60 seconds, otherwise False
def user_is_idle():
    idle = re.sub("[^0-9]", "", str(subprocess.check_output('xprintidle', shell=True)))
    if int(idle) > 60000:
        return True
    else:
        return False


# Waits 5 seconds (default), turns off screen if user still idle
# Runs if user is idle when off endpoint reached, delay gives user
# time to move mouse and keep screen on after other devices turn off
def turn_off_after_delay(seconds=5):
    time.sleep(seconds)
    if user_is_idle():
        os.system('xset dpms force off')


if __name__ == '__main__':
    app.run(host="0.0.0.0")
