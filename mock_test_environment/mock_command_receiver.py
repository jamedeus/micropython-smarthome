#!/usr/bin/python3

# Goal: Simulate all API endpoints used by device and sensor classes
# Allows running tests without real hardware (and without annoyingly turning lights on/off)

import socket
import threading
from struct import pack
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


# Class to simulate TpLink Kasa device, runs in separate thread
class MockTpLink:
    dimmer_response = """{"smartlife.iot.dimmer":{"set_brightness":{"err_code":0}}}"""
    bulb_response = """{"smartlife.iot.smartbulb.lightingservice":{"transition_light_state":{"err_code":0}}}"""

    # Listen for connections on port used by Tplink Kasa
    def serve(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind(("0.0.0.0", 9999))
        server.listen(5)

        while True:
            client, addr = server.accept()
            print(f"New connection from {addr[0]}:{addr[1]}")
            self.handle_client(client)

    # Return response based on request type (dimmer or bulb)
    def handle_client(self, client_socket):
        request = client_socket.recv(1024)
        request = self.decrypt(request[4:])
        print(f"Received: {request}")
        if "smartbulb" in request:
            print(f"Response: {self.bulb_response}\n")
            client_socket.send(self.encrypt(self.bulb_response))
        else:
            print(f"Response: {self.dimmer_response}\n")
            client_socket.send(self.encrypt(self.dimmer_response))
        client_socket.close()

    # Tplink's ridiculously insecure encryption
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


def run_flask():
    app.run(host="0.0.0.0", port=8123)


if __name__ == '__main__':
    # Start Flask app
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.start()

    # Start mock Tplink receiver
    server = MockTpLink()
    tplink_thread = threading.Thread(target=server.serve)
    tplink_thread.start()
