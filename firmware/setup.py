import json
import time
import network
import uasyncio as asyncio
from machine import Timer
from util import reboot
from setup_page import setup_page

reboot_timer = Timer(1)

ap = network.WLAN(network.AP_IF)
wlan = network.WLAN(network.STA_IF)


def test_connection(ssid, password):
    wlan.connect(ssid, password)

    # Try to connect for up to 5 seconds
    fails = 0
    while not wlan.isconnected():
        if fails > 5:
            wlan.disconnect()
            return False
        fails += 1
        time.sleep(1)

    return True


def create_config_file(data):
    if not test_connection(data["ssid"], data["password"]):
        print("Unable to connect to wifi with provided credentials")
        return False

    try:
        # Populate template from received dict keys
        config = {
            "metadata": {
                "id": "",
                "location": "",
                "floor": "",
                "timezone": data["timezone"],
                "schedule_keywords": {}
            },
            "wifi": {
                "ssid": data["ssid"],
                "password": data["password"]
            }
        }

        # Write to disk
        with open('config.json', 'w') as file:
            json.dump(config, file)

        with open('webrepl_cfg.py', 'w') as file:
            file.write(f"PASS = '{data['webrepl']}'")

        return True

    except KeyError:
        return False


async def handle_client(reader, writer):
    request = await reader.read(1024)
    print('Received request:', request)

    # Parse request method from headers
    method = request.split(b' ', 1)[0]

    # POST: Create config file from data, reboot if successful
    if method == b'POST':
        # Parse form data from end of request
        data = request.split(b'\r\n\r\n')[1]
        data = json.loads(data)
        print('Form data:', data)

        # Create config from form data, reboot after 1 second if successful
        if create_config_file(data):
            print("Config file created, rebooting...")
            reboot_timer.init(period=1000, mode=Timer.ONE_SHOT, callback=reboot)
            await writer.awrite('HTTP/1.1 200 OK\r\n\r\n')

        # Return 400 if unable to generate
        else:
            print("ERROR: Failed to create config file")
            await writer.awrite('HTTP/1.1 400 Bad Request\r\n\r\n')

    # GET: Serve setup page
    else:
        # Build script creates setup_page.py (single variable containing contents of setup.html)
        response = f"HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n{setup_page}"
        await writer.awrite(response)

    await writer.aclose()


# Listen for connections on port 80
async def start_server():
    await asyncio.start_server(handle_client, '0.0.0.0', 80, 5)
    while True:
        await asyncio.sleep(25)


# Create access point, listen for connections
def serve_setup_page():
    wlan.active(True)
    ap.active(True)
    asyncio.run(start_server())
