import os
import json
from unittest import TestCase
from unittest.mock import patch, mock_open
from helper_functions import (
    is_device_or_sensor,
    is_device,
    is_sensor,
    is_int,
    is_float,
    is_int_or_float,
    get_cli_config_name,
    get_config_filename,
    get_config_param_list,
    valid_ip,
    valid_uri,
    valid_timestamp,
    get_schedule_keywords_dict,
    load_unit_test_config,
    get_device_and_sensor_metadata,
    celsius_to_fahrenheit,
    celsius_to_kelvin,
    fahrenheit_to_celsius,
    kelvin_to_celsius,
    convert_celsius_temperature
)
from mock_cli_config import mock_cli_config

# Get full path to repository root directory
tests = os.path.split(os.path.dirname(os.path.realpath(__file__)))[0]
repo = os.path.split(tests)[0]

# Read unit-test-config.json from disk
config_path = os.path.join(repo, 'util', 'unit-test-config.json')
with open(config_path, 'r', encoding='utf-8') as file:
    unit_test_config = json.load(file)


class TestHelperFunctions(TestCase):

    def test_is_device_or_sensor(self):
        # Should accept strings that start with device or sensor
        self.assertTrue(is_device_or_sensor("device1"))
        self.assertTrue(is_device_or_sensor("sensor2"))
        # Should reject all other strings
        self.assertFalse(is_device_or_sensor("ir_blaster"))

    def test_is_device(self):
        # Should accept strings that start with device
        self.assertTrue(is_device("device1"))
        # Should reject all other strings
        self.assertFalse(is_device("sensor2"))
        self.assertFalse(is_device("ir_blaster"))

    def test_is_sensor(self):
        # Should accept strings that start with sensor
        self.assertTrue(is_sensor("sensor1"))
        # Should reject all other strings
        self.assertFalse(is_sensor("device2"))
        self.assertFalse(is_sensor("ir_blaster"))

    def test_is_int(self):
        # Should accept integers and strings that cast to integers
        self.assertTrue(is_int(123))
        self.assertTrue(is_int("123"))
        # Should reject all other input
        self.assertFalse(is_int("123.45"))
        self.assertFalse(is_int("abc"))
        self.assertFalse(is_int(None))

    def test_is_float(self):
        # Should accept floats and strings that cast to floats
        self.assertTrue(is_float(123.45))
        self.assertTrue(is_float("123.45"))
        self.assertTrue(is_float("123"))
        # Should reject all other input
        self.assertFalse(is_float("abc"))
        self.assertFalse(is_float(None))

    def test_is_int_or_float(self):
        # Should accept integers, floats, and strings that cast to int/float
        self.assertTrue(is_int_or_float(123))
        self.assertTrue(is_int_or_float("123"))
        self.assertTrue(is_int_or_float(123.45))
        self.assertTrue(is_int_or_float("123.45"))
        # Should reject all other input
        self.assertFalse(is_int_or_float("abc"))
        self.assertFalse(is_int_or_float(None))

    def test_get_cli_config_name(self):
        # Should return string in lowercase with spaces replaced with hyphens
        self.assertEqual(get_cli_config_name("Friendly Name"), "friendly-name")
        self.assertEqual(get_cli_config_name("AnotherName"), "anothername")

    def test_get_config_filename(self):
        # Should return string in lowercase with spaces replaced with hyphens
        # and .json extension
        self.assertEqual(get_config_filename("Friendly Name"), "friendly-name.json")
        self.assertEqual(get_config_filename("AnotherName.json"), "anothername.json")

    def test_get_config_param_list(self):
        # Should return list of device and sensor _type key values
        self.assertEqual(
            get_config_param_list(unit_test_config, "_type"),
            [
                'dimmer',
                'bulb',
                'tasmota-relay',
                'dumb-relay',
                'desktop',
                'pwm',
                'mosfet',
                'wled',
                'api-target',
                'pir',
                'switch',
                'dummy',
                'desktop',
                'si7021'
            ]
        )

        # Should return list of device and sensor pin key values
        self.assertEqual(
            get_config_param_list(unit_test_config, "pin"),
            ['18', '26', '19', '4', '5', '23']
        )

        # Should return list of device and sensor ip key values
        self.assertEqual(
            get_config_param_list(unit_test_config, "ip"),
            [
                '192.168.1.105',
                '192.168.1.106',
                '192.168.1.107',
                '192.168.1.150',
                '192.168.1.110',
                '127.0.0.1',
                '192.168.1.150'
            ]
        )

    def test_valid_ip(self):
        # Should accept any valid IPv4 address (each block between 0-255)
        self.assertTrue(valid_ip("192.168.0.1"))
        self.assertTrue(valid_ip("255.255.255.255"))
        # Should reject if blocks outside 0-255, block missing, contains alpha
        self.assertFalse(valid_ip("256.256.256.256"))
        self.assertFalse(valid_ip("192.168.0"))
        self.assertFalse(valid_ip("abc.def.ghi.jkl"))

    def test_valid_uri(self):
        # Should accept URI with http or https followed by domain or IP
        self.assertTrue(valid_uri("http://example.com"))
        self.assertTrue(valid_uri("https://192.168.0.1"))
        # Should accept URI with ports, subdomains, and paths
        self.assertTrue(valid_uri("https://192.168.0.1:8080/path"))
        self.assertTrue(valid_uri("http://page.example.com/path"))
        # Should reject other protocols, missing values, etc
        self.assertFalse(valid_uri("ftp://example.com"))
        self.assertFalse(valid_uri("http://localhost"))
        self.assertFalse(valid_uri("https://192.168.0"))

    def test_valid_timestamp(self):
        # Should accept HH:MM where HH is between 00-23, MM is between 00-59
        self.assertTrue(valid_timestamp("12:34"))
        self.assertTrue(valid_timestamp("00:00"))
        # Should reject timestamps with hours or minutes out of range
        self.assertFalse(valid_timestamp("24:00"))
        self.assertFalse(valid_timestamp("12:60"))
        # Should reject missing colon
        self.assertFalse(valid_timestamp("1234"))

    def test_get_schedule_keywords_dict(self):
        # Mock open to return mock_cli_config
        mock_file = mock_open(read_data=json.dumps(mock_cli_config))
        with patch('builtins.open', mock_file):
            # Should return schedule_keywords key from cli_config.json
            output = get_schedule_keywords_dict()
            self.assertEqual(output, mock_cli_config['schedule_keywords'])

        # Should return empty dict if cli_config.json does not exist
        with patch('builtins.open', side_effect=FileNotFoundError):
            output = get_schedule_keywords_dict()
            self.assertEqual(output, {})

    def test_load_unit_test_config(self):
        # Should return contents of util/unit-test-config.json
        self.assertEqual(load_unit_test_config(), unit_test_config)

    def test_get_device_and_sensor_metadata(self):
        # Should return dict with device and sensors keys
        metadata = get_device_and_sensor_metadata()
        self.assertIsInstance(metadata, dict)
        self.assertEqual(list(metadata.keys()), ['devices', 'sensors'])

        # Confirm each item in both sections contains expected metadata keys
        for entry in (metadata['devices'] | metadata['sensors']).values():
            self.assertIn('config_name', entry)
            self.assertIn('class_name', entry)
            self.assertIn('display_name', entry)
            self.assertIn('dependencies', entry)
            self.assertIn('config_template', entry)
            self.assertIn('rule_prompt', entry)

    def test_celsius_to_fahrenheit(self):
        # Should convert to fahrenheit and return
        self.assertEqual(celsius_to_fahrenheit(0), 32)
        self.assertEqual(celsius_to_fahrenheit(100), 212)
        self.assertAlmostEqual(celsius_to_fahrenheit(-40), -40)

    def test_celsius_to_kelvin(self):
        # Should convert to kelvin and return
        self.assertEqual(celsius_to_kelvin(0), 273.15)
        self.assertEqual(celsius_to_kelvin(100), 373.15)
        self.assertEqual(celsius_to_kelvin(-273.15), 0)

    def test_fahrenheit_to_celsius(self):
        # Should convert to celsius and return
        self.assertEqual(fahrenheit_to_celsius(32), 0)
        self.assertEqual(fahrenheit_to_celsius(212), 100)
        self.assertAlmostEqual(fahrenheit_to_celsius(-40), -40)

    def test_kelvin_to_celsius(self):
        # Should convert to celsius and return
        self.assertEqual(kelvin_to_celsius(273.15), 0)
        self.assertEqual(kelvin_to_celsius(373.15), 100)
        self.assertEqual(kelvin_to_celsius(0), -273.15)

    def test_convert_celsius_temperature(self):
        # Should convert to requested units and return
        self.assertEqual(convert_celsius_temperature(0, "fahrenheit"), 32)
        self.assertEqual(convert_celsius_temperature(0, "kelvin"), 273.15)
        # Should raise ValueError if invalid units requested
        with self.assertRaises(ValueError):
            convert_celsius_temperature(0, "invalid")
