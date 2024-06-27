import gc
import tls
import json
import socket
import asyncio
import network
import binascii
from machine import Timer
import setup_ssl_certs
from util import reboot
from setup_page import setup_page

reboot_timer = Timer(1)

# Access point interface broadcasts setup network, serves captive portal
# Wlan interface verifies ssid + password received from setup (attempt connection)
ap = network.WLAN(network.WLAN.IF_AP)
wlan = network.WLAN(network.WLAN.IF_STA)

# Create SSL context using cert and key frozen into firmware
ssl_context = tls.SSLContext(tls.PROTOCOL_TLS_SERVER)
ssl_context.load_cert_chain(setup_ssl_certs.CERT, setup_ssl_certs.KEY)


def test_connection(ssid, password):
    wlan.connect(ssid, password)

    # Wait until connection succeeds or fails
    while wlan.status() in (network.STAT_CONNECTING, network.STAT_IDLE):
        pass

    # Return True if connection succeeded
    if wlan.status() == network.STAT_GOT_IP:
        return True

    # Clean up unsuccessful connection and return False
    wlan.disconnect()
    return False


def create_config_file(data):
    try:
        # Confirm credentials are valid before writing to disk
        if not test_connection(data["ssid"], data["password"]):
            print("Unable to connect to wifi with provided credentials")
            return False

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


# Redirect all HTTP requests to port 443
async def handle_http_client(reader, writer):
    request = await reader.read(1024)
    print('Received HTTP request:', request)

    # Serve page with meta refresh tag to redirect to HTTPS
    print("Serving redirect page")
    writer.write(b'HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n')
    writer.write(b'<html><head><meta http-equiv="refresh" content="0; url=https://192.168.4.1:443/"></head>')
    writer.write(b'<body><script>window.location="https://192.168.4.1:443/";</script>')
    writer.write(b'<a href="https://192.168.4.1:443/">Click here if you are not redirected</a></body></html>\r\n')
    await writer.drain()
    await writer.aclose()


async def handle_https_client(reader, writer):
    try:
        request = await reader.read(1024)
        print('Received HTTPS request:', request)

        # Parse request method from headers
        method = request.split(b' ', 1)[0]

        # POST: Create config file from data, reboot if successful
        if method == b'POST':
            # Parse form data from end of request
            data = request.split(b'\r\n\r\n')[1]
            data = json.loads(data)
            print('Form data:', data)

            # Create config from form data, reboot after 15 seconds if successful
            if create_config_file(data):
                # Post node IP to frontend (displayed in success animation)
                response = json.dumps({"ip": wlan.ifconfig()[0]})
                writer.write(b'HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n\r\n')
                writer.write(response)
                await writer.drain()

                print("Config file created, rebooting...")
                reboot_timer.init(period=15000, mode=Timer.ONE_SHOT, callback=reboot)

            # Return 400 if unable to generate
            else:
                print("ERROR: Failed to create config file")
                writer.write('HTTP/1.1 400 Bad Request\r\n\r\n')
                await writer.drain()

        # GET: Serve setup page (setup script creates setup_page.py with single
        # variable containing contents of setup.html + compiled CSS)
        else:
            print("Serving setup page")
            writer.write(b'HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n')
            writer.write(b'Strict-Transport-Security: max-age=31536000; includeSubDomains; preload\r\n\r\n')
            writer.write(setup_page)
            await writer.drain()

        await writer.aclose()

    # Silence errors from client disconnecting early
    except OSError:
        pass


# Respond to all DNS queries with setup page IP
# Port defaults to 53, only changed in unit tests
async def run_captive_portal(port=53):
    # Create non-blocking UDP socket (avoid blocking event loop)
    udps = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udps.setblocking(False)
    udps.bind(('0.0.0.0', port))

    while True:
        try:
            gc.collect()
            data, addr = udps.recvfrom(4096)
            response = dns_redirect(data, '192.168.4.1')
            udps.sendto(response, addr)
            print("Sending captive portal redirect")
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


def serve_setup_page():
    # Append last byte of access point mac address to SSID
    mac_address = binascii.hexlify(ap.config('mac')).decode()
    ap.config(ssid=f'Smarthome_Setup_{mac_address.upper()[-4:]}')

    # Set IP, subnet, gateway, DNS
    ap.ifconfig(('192.168.4.1', '255.255.255.0', '192.168.4.1', '192.168.4.1'))

    # Power on wifi + access point interfaces
    wlan.active(True)
    ap.active(True)

    # Do not retry failed connection (slows down connection test)
    wlan.config(reconnects=0)

    loop = asyncio.get_event_loop()

    # Listen for TCP connections on port 80, redirect to port 443
    loop.create_task(asyncio.start_server(handle_http_client, '0.0.0.0', 80))
    # Serve setup page on port 443 with SSL
    loop.create_task(asyncio.start_server(handle_https_client, "0.0.0.0", 443, 5, ssl=ssl_context))
    # Listen for DNS queries on port 53, redirect to setup page
    loop.create_task(run_captive_portal())
    loop.run_forever()
