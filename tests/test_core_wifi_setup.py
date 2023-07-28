import os
import json
import asyncio
import network
import unittest
from setup_page import setup_page
from unittest.mock import patch, Mock, AsyncMock
from util import read_config_from_disk, write_config_to_disk
from wifi_setup import test_connection, create_config_file, handle_client, dns_redirect, serve_setup_page

# Read mock API receiver address
with open('config.json', 'r') as file:
    config = json.load(file)

ap = network.WLAN(network.AP_IF)
wlan = network.WLAN(network.STA_IF)


# Used to simulate DNS request to captive portal
class DnsRequestClient(asyncio.DatagramProtocol):
    # Takes message (DNS request) and pending future
    def __init__(self, message, future):
        super().__init__()
        self.message = message
        self.future = future

    # Send message to server
    def connection_made(self, transport):
        self.transport = transport
        print('Send:', self.message)
        self.transport.sendto(self.message)

    # Add response to future, close socket
    def datagram_received(self, data, addr):
        print("Received:", data)
        self.future((data, addr))  # Wrap data and addr in a tuple
        self.transport.close()


# Simulates DNS query to run_captive_portal task in test script
async def send_dns_query():
    # Pending future to receive response from UDP socket
    future = asyncio.Future()

    # Instantiate with DNS query as message, future to receive response
    query = b'u\xec\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00\x0cdetectportal\x07firefox\x03com\x00\x00\x1c\x00\x01'
    protocol = DnsRequestClient(query, future.set_result)

    # Open UDP connection to run_captive_portal task started in test script
    loop = asyncio.get_running_loop()
    transport, _ = await loop.create_datagram_endpoint(
        lambda: protocol,
        remote_addr=('127.0.0.1', 8316))

    # Return response
    response = await future  # Unpack data and addr from the result
    return response


class WifiSetupTests(unittest.TestCase):

    def test_01_test_connection(self):
        # Should return True if connection succeeds
        self.assertTrue(test_connection(config['wifi']['ssid'], config['wifi']['password']))

        # Should return False if connection fails
        self.assertFalse(test_connection('wrong', 'invalid'))

    def test_02_test_create_config_file(self):
        # Backup actual config file, delete
        backup = read_config_from_disk()
        os.remove('config.json')

        # Simulated payload from setup page
        payload = {
            'ssid': 'mynetwork',
            'password': 'hunter2',
            'webrepl': 'password'
        }

        # Call method, should return True
        self.assertTrue(create_config_file(payload))

        # Confirm config created with correct params
        output = read_config_from_disk()
        self.assertEqual(output['wifi']['ssid'], 'mynetwork')
        self.assertEqual(output['wifi']['password'], 'hunter2')

        # Should return False if wifi ssid/pass is incorrect
        payload['ssid'] = 'wrong'
        self.assertFalse(create_config_file(payload))

        # Should return False if key missing from payload
        del payload['ssid']
        self.assertFalse(create_config_file(payload))

        # Overwrite with original config file
        write_config_to_disk(backup)

    def test_03_dns_redirect(self):
        # Captive portal DNS query
        query = b'u\xec\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00\x0cdetectportal\x07firefox\x03com\x00\x00\x1c\x00\x01'

        # Simulate 192.168.1.100 making query, confirm correct redirect response
        redirect = dns_redirect(query, '192.168.4.1')
        self.assertEqual(
            redirect,
            b'u\xec\x81\x80\x00\x01\x00\x01\x00\x00\x00\x00\x0cdetectportal\x07firefox\x03com\x00\x00\x1c\x00\x01\xc0\x0c\x00\x01\x00\x01\x00\x00\x00<\x00\x04\xc0\xa8\x04\x01'
        )

    # TODO prevent running on micropython
    def test_04_serve_setup_page(self):
        # Mock all methods so function returns immediately
        with patch('wifi_setup.handle_client'), \
             patch('wifi_setup.run_captive_portal'), \
             patch('wifi_setup.keep_alive'), \
             patch('wifi_setup.asyncio.start_server'):

            # Run function
            serve_setup_page()

        # Confirm network adapters configured correctly
        self.assertTrue(ap.active())
        self.assertTrue(wlan.active())
        self.assertEqual(wlan.config('reconnects'), 0)
        self.assertEqual(ap.config('ssid'), 'Smarthome_Setup_AEE9')
        self.assertEqual(ap.ifconfig(), ('192.168.4.1', '255.255.255.0', '192.168.4.1', '192.168.4.1'))

    # TODO prevent running on micropython
    def test_05_handle_client_get(self):
        # Create mock stream handlers simulating GET request
        mock_reader = AsyncMock()
        mock_writer = AsyncMock()
        request = b'GET / HTTP/1.1\r\n\r\n'
        mock_reader.read = asyncio.coroutine(Mock(return_value=request))

        # Simulate connection, confirm correct response (serve setup page)
        loop = asyncio.get_event_loop()
        loop.run_until_complete(handle_client(mock_reader, mock_writer))
        mock_writer.awrite.assert_called_once_with(f"HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n{setup_page}")

    # TODO prevent running on micropython
    def test_06_handle_client_post(self):
        # Create mock stream handlers simulating POST request with invalid JSON
        mock_reader = AsyncMock()
        mock_writer = AsyncMock()
        request = b'POST / HTTP/1.1\r\n\r\n{"data": "value"}'
        mock_reader.read = asyncio.coroutine(Mock(return_value=request))

        # Simulate connection, confirm correct error
        with patch('wifi_setup.create_config_file', return_value=False):
            loop = asyncio.get_event_loop()
            loop.run_until_complete(handle_client(mock_reader, mock_writer))
            mock_writer.awrite.assert_called_once_with('HTTP/1.1 400 Bad Request\r\n\r\n')

        mock_writer.reset_mock()

        # Simulate connection with valid JSON payload, confirm correct response
        with patch('wifi_setup.create_config_file', return_value=True):
            loop = asyncio.get_event_loop()
            loop.run_until_complete(handle_client(mock_reader, mock_writer))
            mock_writer.awrite.assert_called_once_with('HTTP/1.1 200 OK\r\n\r\n')

    # TODO prevent running on micropython
    def test_07_captive_portal(self):
        # Simulate DNS query to run_captive_portal task in test script
        response = asyncio.run(send_dns_query())

        # Should return tuple containing redirect and address
        self.assertTrue(isinstance(response, tuple))
        self.assertEqual(
            response[0],
            b'u\xec\x81\x80\x00\x01\x00\x01\x00\x00\x00\x00\x0cdetectportal\x07firefox\x03com\x00\x00\x1c\x00\x01\xc0\x0c\x00\x01\x00\x01\x00\x00\x00<\x00\x04\xc0\xa8\x04\x01'
        )
        self.assertEqual(response[1], ('127.0.0.1', 8316))
