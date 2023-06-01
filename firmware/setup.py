import json
import network
import uasyncio as asyncio
from machine import Timer
from util import reboot
from setup_page import setup_page

reboot_timer = Timer(1)


def create_config_file(data):
    try:
        # Populate template from received dict keys
        config = {
            "metadata": {
                "id": "",
                "location": "",
                "floor": "",
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
        else:
            print("ERROR: Failed to create config file")

        await writer.awrite('HTTP/1.1 200 OK\r\n\r\n')

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
    ap = network.WLAN(network.AP_IF)
    ap.active(True)
    asyncio.run(start_server())
