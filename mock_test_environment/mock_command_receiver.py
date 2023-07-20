#!/usr/bin/python3

# Goal: Simulate all API endpoints used by device and sensor classes
# Allows running tests without real hardware (and without annoyingly turning lights on/off)

from flask import Flask, request

app = Flask(__name__)

# Store state between requests
tasmota_relay_last = "ON"
wled_brightness = 255
wled_state = 1
desktop_state = 'On'


# Tasmota relay mock
@app.route('/cm')
def tasmota_relay():
    global tasmota_relay_last
    cmd = request.args.get('cmnd')

    # Check power state
    if cmd == "Power":
        return {"POWER": tasmota_relay_last}

    # Turn on
    elif cmd == "Power On":
        tasmota_relay_last = "ON"
        return {"POWER": tasmota_relay_last}

    # Turn off
    elif cmd == "Power Off":
        tasmota_relay_last = "OFF"
        return {"POWER": tasmota_relay_last}

    else:
        return {"Command": "Unknown"}


# WLED mock
@app.route('/win')
def wled():
    global wled_brightness
    global wled_state
    wled_brightness = request.args.get('A')
    wled_state = request.args.get('T')

    # Turn on
    if wled_state:
        return f'<?xml version="1.0" ?><vs><ac>{wled_brightness}</ac><cl>255</cl><cl>160</cl><cl>0</cl><cs>0</cs><cs>0</cs><cs>0</cs><ns>0</ns><nr>1</nr><nl>0</nl><nf>1</nf><nd>60</nd><nt>0</nt><fx>97</fx><sx>128</sx><ix>255</ix><fp>11</fp><wv>-1</wv><ws>0</ws><ps>1</ps><cy>0</cy><ds>WLED</ds><ss>0</ss></vs>'.encode()

    # Turn off
    else:
        return b'<?xml version="1.0" ?><vs><ac>0</ac><cl>255</cl><cl>160</cl><cl>0</cl><cs>0</cs><cs>0</cs><cs>0</cs><ns>0</ns><nr>1</nr><nl>0</nl><nf>1</nf><nd>60</nd><nt>0</nt><fx>97</fx><sx>128</sx><ix>255</ix><fp>11</fp><wv>-1</wv><ws>0</ws><ps>1</ps><cy>0</cy><ds>WLED</ds><ss>0</ss></vs>'


# Desktop integration - get monitor state
@app.get("/state")
def get_dpms_state():
    global desktop_state
    return {'state': desktop_state}, 200


# Desktop integration - get idle time
@app.get("/idle_time")
def get_idle_time():
    return {'idle_time': 523}, 200


# Desktop integration - turn screen on
@app.get("/on")
def monitor_on():
    global desktop_state
    desktop_state = 'On'
    return {'state': 'on'}, 200


# Desktop integration - turn screen off
@app.get("/off")
def monitor_off():
    global desktop_state
    desktop_state = 'Off'
    return {'state': 'off'}, 200


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8123)
