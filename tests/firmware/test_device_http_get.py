import re
import sys
import unittest
from cpython_only import cpython_only
from HttpGet import HttpGet, uri_pattern

# Import dependencies for tests that only run in mocked environment
if sys.implementation.name == 'cpython':
    import requests
    from unittest.mock import patch


class TestHttpGet(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Instantiate with mock URI and on/off paths (send calls will be mocked)
        cls.instance = HttpGet("device1", "device1", "HttpGet", "Enabled", "http://192.168.1.100", "on", "off")

    def test_01_initial_state(self):
        # Confirm attributes, confirm http removed from URI
        self.assertIsInstance(self.instance, HttpGet)
        self.assertEqual(self.instance.uri, '192.168.1.100')
        self.assertEqual(self.instance.on_path, 'on')
        self.assertEqual(self.instance.off_path, 'off')

    def test_02_instantiate_with_invalid_uri(self):
        # AttributeError should be raised if instantiated with an invalid URI
        with self.assertRaises(AttributeError):
            HttpGet("device1", "device1", "HttpGet", "Enabled", "192.168.1.", "on", "off")

    def test_03_uri_pattern(self):
        # Should accept domain or IP with no port number
        self.assertTrue(re.match(uri_pattern, 'test.com'))
        self.assertTrue(re.match(uri_pattern, 'sub.domain.com'))
        self.assertTrue(re.match(uri_pattern, '123.45.67.89'))
        self.assertTrue(re.match(uri_pattern, '192.168.1.100'))
        # Should accept with port number
        self.assertTrue(re.match(uri_pattern, 'test.com:8000'))
        self.assertTrue(re.match(uri_pattern, 'sub.domain.com:8123'))
        self.assertTrue(re.match(uri_pattern, '123.45.67.89:6500'))
        self.assertTrue(re.match(uri_pattern, '192.168.1.100:9999'))

    def test_04_get_url(self):
        # Get on URL, confirm correct
        url = self.instance.get_url(1)
        self.assertEqual(url, 'http://192.168.1.100/on')
        # Get off URL, confirm correct
        url = self.instance.get_url(0)
        self.assertEqual(url, 'http://192.168.1.100/off')

    @cpython_only
    def test_05_send_method(self):
        # Build mock response object
        response = requests.Response()
        response.status_code = 200

        # Confirm send method calls requests.get with correct URI and path
        with patch.object(requests, 'get', return_value=response) as mock_request:
            # Turn on, should return True, confirm correct arg passed
            self.assertTrue(self.instance.send(1))
            self.assertTrue(mock_request.called_once)
            self.assertEqual(mock_request.call_args_list[0][0][0], 'http://192.168.1.100/on')

        # Repeat with off command, confirm called with correct URI and path
        with patch.object(requests, 'get', return_value=response) as mock_request:
            # Turn off, should return True, confirm correct arg passed
            self.assertTrue(self.instance.send(0))
            self.assertTrue(mock_request.called_once)
            self.assertEqual(mock_request.call_args_list[0][0][0], 'http://192.168.1.100/off')

        # Confirm send method returns False when request fails
        response.status_code = 500
        with patch.object(requests, 'get', return_value=response) as mock_request:
            self.assertFalse(self.instance.send(1))
            self.assertTrue(mock_request.called_once)
            self.assertEqual(mock_request.call_args_list[0][0][0], 'http://192.168.1.100/on')

    # Original bug: get_url concatenates URI and on/off_path separated by
    # a forward slash (/). If on/off_path already started with a forward
    # slash this added an extra slash (//), which causes 404 error on some
    # target devices. Init method now removes leading forward slash.
    def test_06_regression_double_forward_slash(self):
        # Instantiate with forward slash on both paths
        test = HttpGet("device1", "device1", "HttpGet", "Enabled", "http://192.168.1.100", "/on", "/off")
        # Confirm forward slashes were removed
        self.assertEqual(test.on_path, 'on')
        self.assertEqual(test.off_path, 'off')
