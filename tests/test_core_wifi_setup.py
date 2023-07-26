import os
import json
import unittest
from util import read_config_from_disk, write_config_to_disk
from wifi_setup import test_connection, create_config_file, dns_redirect

# Read mock API receiver address
with open('config.json', 'r') as file:
    config = json.load(file)


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
