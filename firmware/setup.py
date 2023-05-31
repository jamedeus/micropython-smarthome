import json
import network
import uasyncio as asyncio
from machine import Timer
from util import reboot

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
        response = """HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>WiFi Connection Page</title>
    <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
</head>
<body class="flex items-center justify-center h-screen bg-gray-200">
    <form class="text-center" action="" id="configuration" method="post">
        <div class="bg-white p-8 rounded-lg shadow-md w-96 mb-6">
            <h1 class="text-2xl font-bold mb-6 text-center text-gray-700">WiFi Credentials</h1>

            <div class="mb-4">
                <input class="text-center shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent" id="ssid" name="ssid" type="text" placeholder="SSID">
            </div>
            <div class="mb-6">
                <input class="text-center shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent" id="password" name="password" type="password" placeholder="Password">
            </div>
        </div>

        <div class="flex items-center justify-between mb-6">
            <input class="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 mx-auto rounded focus:outline-none focus:shadow-outline" type="submit" value="Connect">
        </div>
    </form>
    <script>
        document.getElementById('configuration').addEventListener('submit', function(e) {
            e.preventDefault();

            var formData = {};
            new FormData(e.target).forEach(function(value, name) {
                formData[name] = value;
            });

            fetch('', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(formData)
            });
        });
    </script>
</body>
</html>
"""
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
