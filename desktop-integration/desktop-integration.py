#!/usr/bin/python3

import re
import os
import subprocess
from flask import Flask

app = Flask(__name__)


@app.get("/state")
def get_dpms_state():
    # Query DPMS state (monitors on/off/standby etc)
    try:
        current = subprocess.check_output('xset -q | tail -1 | cut -d " " -f 5', shell=True, stderr=subprocess.STDOUT)
        current = str(current)[2:-3]
        return {'state': current}, 200
    except Exception as ex:
        return {'Error': ex}, 500


@app.get("/idle_time")
def get_idle_time():
    try:
        idle = re.sub("[^0-9]", "", str(subprocess.check_output('xprintidle', shell=True)))
        return {'idle_time': idle}, 200
    except Exception as ex:
        return {'Error': ex}, 500


@app.get("/on")
def monitor_on():
    try:
        os.system('xset dpms force on')
        return {'state': 'on'}, 200
    except Exception as ex:
        return {'Error': ex}, 500


@app.get("/off")
def monitor_off():
    try:
        os.system('xset dpms force off')
        return {'state': 'off'}, 200
    except Exception as ex:
        return {'Error': ex}, 500


if __name__ == '__main__':
    app.run(host="0.0.0.0")
