import os
import json
import unittest
from machine import reset
from util import (
    is_device,
    is_sensor,
    is_device_or_sensor,
    read_config_from_disk,
    write_config_to_disk,
    reboot,
    clear_log,
    check_log_size
)
from cpython_only import cpython_only

# Read config file from disk
with open('config.json', 'r') as file:
    config = json.load(file)


class TestUtil(unittest.TestCase):

    def test_01_is_device(self):
        # Should return True for strings beginning with "device"
        self.assertTrue(is_device('device1'))
        # Should return False for other strings
        self.assertFalse(is_device('sensor3'))
        self.assertFalse(is_device('group2'))
        # Should return False for non-strings
        self.assertFalse(is_device({'key': 'val'}))

    def test_02_is_sensor(self):
        # Should return True for strings beginning with "sensor"
        self.assertTrue(is_sensor('sensor1'))
        # Should return False for other strings
        self.assertFalse(is_sensor('device3'))
        self.assertFalse(is_sensor('group2'))
        # Should return False for non-strings
        self.assertFalse(is_sensor({'key': 'val'}))

    def test_03_is_device_or_sensor(self):
        # Should return True for strings beginning with "device" or "sensor"
        self.assertTrue(is_device_or_sensor('device1'))
        self.assertTrue(is_device_or_sensor('sensor1'))
        # Should return False for other strings
        self.assertFalse(is_device_or_sensor('group2'))
        # Should return False for non-strings
        self.assertFalse(is_device_or_sensor({'key': 'val'}))

    def test_04_read_config_from_disk(self):
        config_file = read_config_from_disk()
        self.assertIsInstance(config_file, dict)

    def test_05_write_config_to_disk(self):
        # Delete config from disk, confirm removed
        os.remove('config.json')
        self.assertFalse('config.json' in os.listdir())

        # Write config back to disk, confirm written
        self.assertTrue(write_config_to_disk(config))
        self.assertTrue('config.json' in os.listdir())

        # Should refuse to write non-dict
        self.assertFalse(write_config_to_disk("string"))

    @cpython_only
    def test_06_reboot(self):
        # Function should call machine.reset
        reset.called = False
        self.assertFalse(reset.called)
        reboot()
        self.assertTrue(reset.called)

    @cpython_only
    def test_07_clear_log(self):
        # Ensure log file exists on disk
        open('app.log', 'w')
        self.assertTrue('app.log' in os.listdir())

        # Clear log, confirm no longer exists
        clear_log()
        # TODO fails on micropython
        self.assertFalse('app.log' in os.listdir())

    @cpython_only
    def test_08_check_log_size(self):
        # Create mock log file with size 100001 bytes
        with open('app.log', 'wb') as f:
            f.write(os.urandom(100001))
        self.assertEqual(os.stat('app.log')[6], 100001)

        # Run function, confirm log deleted and re-created
        check_log_size()
        self.assertLessEqual(os.stat('app.log')[6], 100)
