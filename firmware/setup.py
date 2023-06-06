import gc
import json
import time
import socket
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

        # Write webrepl password to disk
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


# Respond to all DNS queries with setup page IP
async def run_captive_portal():
    # Create non-blocking UDP socket (avoid blocking event loop)
    udps = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udps.setblocking(False)
    udps.bind(('0.0.0.0', 53))

    while True:
        try:
            gc.collect()
            data, addr = udps.recvfrom(4096)
            response = dns_redirect(data, '192.168.4.1')
            udps.sendto(response, addr)
            await asyncio.sleep_ms(100)

        # Raises "[Errno 11] EAGAIN" if timed out with no connection
        except:
            await asyncio.sleep_ms(3000)


# Takes DNS query + arbitrary IP address, returns DNS response pointing to IP
def dns_redirect(query, ip):
    # Copy transaction ID, add response flags
    response = query[:2] + b'\x81\x80'
    # Copy QDCOUNT, ANCOUNT, NSCOUNT, ARCOUNT, add placeholder bytes
    response += query[4:6] + query[4:6] + b'\x00\x00\x00\x00'
    # Copy remaining bytes from original query
    response += query[12:]
    # Response: Add pointer to domain name, A record, IN class, 60 sec TTL
    response += b'\xc0\x0c\x00\x01\x00\x01\x00\x00\x00\x3c'
    # Set response length to 4 bytes, add IP address
    response += b'\x00\x04'
    response += bytes(map(int, ip.split('.')))
    return response


async def keep_alive():
    while True:
        await asyncio.sleep(25)


def serve_setup_page():
    # Power on wifi + access point interfaces
    wlan.active(True)
    ap.active(True)

    # Set IP, subnet, gateway, DNS
    ap.ifconfig(('192.168.4.1', '255.255.255.0', '192.168.4.1', '192.168.4.1'))

    # Listen for TCP connections on port 80, serve setup page
    # Listen for DNS queries on port 53, redirect to setup page
    asyncio.create_task(asyncio.start_server(handle_client, "0.0.0.0", 80, 5))
    asyncio.create_task(run_captive_portal())
    asyncio.run(keep_alive())
