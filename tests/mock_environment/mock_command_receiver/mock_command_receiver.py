#!/usr/bin/python3

# Goal: Simulate all API endpoints used by device and sensor classes
# Allows running tests without real hardware (and without annoyingly turning lights on/off)

import os
import json
import socket
import asyncio
import threading
from struct import pack
from flask import Flask, request, Response

app = Flask(__name__)

# Store state between requests
tasmota_relay_last = "ON"
wled_brightness = 255
wled_state = 1
desktop_state = 'On'
desktop_idle_time = 0


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


# Set desktop screen state for unit tests
@app.post("/set_screen_state")
def set_screen_state():
    data = request.get_json()
    global desktop_state
    desktop_state = data['state']
    return {'state': desktop_state}, 200


# Desktop integration - get idle time (returns value set with /set_idle_time)
@app.get("/idle_time")
def get_idle_time():
    global desktop_idle_time
    return {'idle_time': desktop_idle_time}, 200


# Set desktop idle time for unit tests
@app.post("/set_idle_time")
def set_idle_time():
    data = request.get_json()
    global desktop_idle_time
    desktop_idle_time = data['idle_time']
    return {'idle_time': desktop_idle_time}, 200


# Desktop integration - turn screen on
@app.get("/on")
def monitor_on():
    global desktop_state
    desktop_state = 'On'
    return {'state': 'on'}, 200


# Desktop integration - turn screen off
@app.get("/off")
def monitor_off():
    global desktop_idle_time
    if desktop_idle_time > 60000:
        global desktop_state
        desktop_state = 'Off'
        return {'state': 'off'}, 200
    else:
        return {'state': 'user not idle'}, 503


# Desktop integration - simulate dpms Disabled
@app.get("/Disabled")
def monitor_Disabled():
    global desktop_state
    desktop_state = 'Disabled'
    return {'state': 'Disabled'}, 200


# Class to simulate TpLink Kasa device, runs in separate thread
class MockTpLink:
    dimmer_state_response = """{"system":{"set_relay_state":{"err_code":0}}}"""
    dimmer_brightness_response = """{"smartlife.iot.dimmer":{"set_brightness":{"err_code":0}}}"""
    bulb_response = """{"smartlife.iot.smartbulb.lightingservice":{"transition_light_state":{"err_code":0}}}"""

    # Listen for connections on port used by Tplink Kasa
    def serve(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind(("0.0.0.0", 9999))
        server.listen(5)

        while True:
            try:
                client, addr = server.accept()
                print(f"New connection from {addr[0]}:{addr[1]}")
                self.handle_client(client)
            except (ConnectionResetError, BrokenPipeError):
                print("ERROR: Connection reset by peer")
                pass

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
            print(f"Received: {request}")
            print(f"Response: {self.dimmer_brightness_response}\n")
            client_socket.send(self.encrypt(self.dimmer_state_response))

            # Wait for second API call, send response
            request = client_socket.recv(1024)
            request = self.decrypt(request[4:])
            print(f"Received: {request}")
            print(f"Response: {self.dimmer_brightness_response}\n")
            client_socket.send(self.encrypt(self.dimmer_brightness_response))

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


# Create second flask app that returns error for all requests
# Used for coverage of error handling lines
error_app = Flask(__name__)
error_type = 400


@error_app.get("/set_bad_request_error")
def set_bad_request_error():
    '''Sets the catchall error route to return 400 error'''
    global error_type
    error_type = 400
    return "Done", 200


@error_app.get("/set_unexpected_json_error")
def set_unexpected_json_error():
    '''Sets the catchall error route to return unexpected JSON with status 200'''
    global error_type
    error_type = 200
    return "Done", 200


# Match all paths
@error_app.route('/<path:path>', methods=['GET', 'POST', 'PUT'])
def catch_all(path):
    global error_type
    if error_type == 200:
        return Response({"unexpected": "json"}, status=200)
    return Response("Bad request", status=400)


def run_flask():
    app.run(host="0.0.0.0", port=int(os.environ.get('PORT')))


def run_error_flask():
    error_app.run(host="0.0.0.0", port=int(os.environ.get('ERROR_PORT')))


# Mock API receiver for ApiTarget tests
class MockApi:
    def __init__(self, host='0.0.0.0', port=int(os.environ.get('API_PORT'))):
        self.host = host
        self.port = port

        self.valid_endpoints = [
            'enable',
            'disable',
            'reset_rule',
            'condition_met',
            'trigger_sensor',
            'turn_on',
            'turn_off',
            'enable_in',
            'disable_in',
            'set_rule',
            'ir_key'
        ]

    async def run(self):
        self.server = await asyncio.start_server(self.run_client, host=self.host, port=self.port, backlog=5)
        print('API: Awaiting client connection.\n')

    async def run_client(self, sreader, swriter):
        try:
            # Read client request (1 second timeout)
            req = await asyncio.wait_for(sreader.readline(), 1)

            # Receives null when client closes write stream - break and close read stream
            if not req:
                raise OSError

            # Parse endpoint and args
            data = json.loads(req)
            path = data[0]
            args = data[1:]
            print(f"MockApi: Received request, endpoint={path}, args={args}")

            # Arbitrary keyword used to trigger OSError in ApiTarget.request
            if path == "raise_exception":
                print("Simulating connection failure")
                swriter.close()
                await swriter.wait_closed()
                return

            # Send arbitrary success message if endpoint is valid, ignore arg
            elif path in self.valid_endpoints:
                swriter.write(json.dumps({path: "Success"}).encode())

            # Otherwise send error
            else:
                swriter.write(json.dumps({"ERROR": "Invalid command"}).encode())
            await swriter.drain()

        except (OSError, asyncio.TimeoutError):
            pass

        # Close socket after client disconnects
        swriter.close()
        await swriter.wait_closed()


def serve_api():
    api = MockApi()
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(api.run())
    loop.run_forever()


if __name__ == '__main__':
    # Start Flask app
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.start()

    # Start error Flask app
    error_flask_thread = threading.Thread(target=run_error_flask)
    error_flask_thread.start()

    # Start mock Tplink receiver
    server = MockTpLink()
    tplink_thread = threading.Thread(target=server.serve)
    tplink_thread.start()

    # Start mock Api receiver
    api_thread = threading.Thread(target=serve_api)
    api_thread.start()
