#!/usr/bin/python3

# Goal: Simulate all API endpoints used by device and sensor classes
# Allows running tests without real hardware (and without annoyingly turning lights on/off)

import os
import json
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
@app.route('/json/state', methods=['GET', 'POST'])
def wled():
    global wled_brightness
    global wled_state

    # Get: Return state information
    if request.method == 'GET':
        return json.dumps({'on': wled_state, 'bri': wled_brightness})

    # Post set brightness and/or power state
    elif request.method == 'POST':
        # Read body even if headers missing
        payload = request.get_json(force=True)
        wled_state = bool(payload["on"])
        try:
            bright = int(payload["bri"])
            if bright > 255:
                # This behavior diverges from WLED, but is necessary to
                # simulate failed requests for full coverage
                return b'{"error":9}', 400
            wled_brightness = int(payload["bri"])
        except (ValueError, TypeError):
            pass
        return b'{"success":true}', 200

    else:
        return b'{"error":9}', 200


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

        # Smartbulb uses a single API call for brightness and power state
        if "smartbulb" in request:
            print(f"Response: {self.bulb_response}\n")
            client_socket.send(self.encrypt(self.bulb_response))

        # Dimmer uses 2 separate API calls for brightness and power state
        else:
            # Send response for first API call
            client_socket.send(self.encrypt({}))

            # Wait for second API call, send response
            request = client_socket.recv(1024)
            request = self.decrypt(request[4:])
            print(f"Received: {request}")
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
    app.run(host="0.0.0.0", port=int(os.environ.get('PORT')))


if __name__ == '__main__':
    # Start Flask app
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.start()

    # Start mock Tplink receiver
    server = MockTpLink()
    tplink_thread = threading.Thread(target=server.serve)
    tplink_thread.start()
