#!/usr/bin/python3

'''Daemon used to integrate a linux computer with micropython-smarthome.

Provides endpoints used by the DesktopTarget device driver to turn the computer
screen on and off in response to sensor conditions.

Provides endpoints used by the DesktopTrigger sensor driver to check if a user
is using the computer. The sensor condition is met while the user is active
(turn target devices on). When user is no longer active devices will turn off.
'''

import re
import os
import time
import threading
import subprocess
from flask import Flask

app = Flask(__name__)


def get_idle_ms():
    '''Returns time (milliseconds) since last mouse or keyboard input'''
    return subprocess.check_output('xprintidle', shell=True)


def user_is_idle():
    '''Returns True if no mouse or keyboard activity in the last 60 seconds,
    returns False if user was active within the last 60 seconds.
    '''
    idle = re.sub("[^0-9]", "", str(get_idle_ms()))
    if int(idle) > 60000:
        return True
    return False


def turn_off_after_delay(seconds=5):
    '''Turns screen off after a 5 second (default) delay if user is still idle.
    Called by the /off endpoint if user idle when request received. The delay
    gives user a change to move mouse and keep screen on (may appear idle while
    watching a video or other activity that doesn't require mouse/keyboard).
    '''
    time.sleep(seconds)
    if user_is_idle():
        os.system('xset dpms force off')


@app.get("/state")
def get_dpms_state():
    '''API endpoint, returns current DPMS state (On, Off, Standby, Disabled)'''
    try:
        current = subprocess.check_output(
            'xset -q | tail -1 | cut -d " " -f 5',
            shell=True,
            stderr=subprocess.STDOUT
        )
        current = str(current)[2:-3]
        return {'state': current}, 200
    except Exception as ex:
        return {'Error': str(ex)}, 500


@app.get("/idle_time")
def get_idle_time():
    '''API endpoint, returns milliseconds since last keyboard/mouse input'''
    try:
        idle = re.sub("[^0-9]", "", str(get_idle_ms()))
        return {'idle_time': idle}, 200
    except Exception as ex:
        return {'Error': str(ex)}, 500


@app.get("/on")
def monitor_on():
    '''API endpoint, turns screen on'''
    try:
        os.system('xset dpms force on')
        return {'state': 'on'}, 200
    except Exception as ex:
        return {'Error': str(ex)}, 500


@app.get("/off")
def monitor_off():
    '''API endpoint, turns screen off after 5 second delay if user is idle'''
    try:
        # Only turn off if no user activity in last 60 seconds
        if user_is_idle():
            # Start 5 second countdown, turn off screen if user still idle
            # Gives user a chance to move mouse and keep screen on
            thread = threading.Thread(target=turn_off_after_delay)
            thread.start()
            return {'state': 'off'}, 200
        return {'state': 'user not idle'}, 503
    except Exception as ex:
        return {'Error': str(ex)}, 500


if __name__ == '__main__':
    app.run(host="0.0.0.0")
