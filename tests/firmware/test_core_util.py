import os
import json
import asyncio
import unittest
from machine import reset
from util import (
    is_device,
    is_sensor,
    is_device_or_sensor,
    read_config_from_disk,
    write_config_to_disk,
    write_ir_macros_to_disk,
    reboot,
    clear_log,
    check_log_size
)
import app_context
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

    def test_06_write_ir_macros_to_disk(self):
        # Delete macros from disk, confirm removed
        if 'ir_macros.json' in os.listdir():
            os.remove('ir_macros.json')
        self.assertFalse('ir_macros.json' in os.listdir())

        # Write mock macros to disk, confirm written
        self.assertTrue(write_ir_macros_to_disk(
            {"macro_name": ["samsung_tv power 500 1"]}
        ))
        self.assertTrue('ir_macros.json' in os.listdir())
        os.remove('ir_macros.json')

        # Should refuse to write non-dict
        self.assertFalse(write_ir_macros_to_disk("string"))

    @cpython_only
    def test_07_reboot(self):
        # Function should call machine.reset
        reset.called = False
        self.assertFalse(reset.called)
        reboot()
        self.assertTrue(reset.called)

    def test_08_clear_log(self):
        # Ensure log file exists on disk, is not empty
        with open('app.log', 'w') as file:
            file.write('test')
        self.assertGreaterEqual(os.stat('app.log')[6], 1)

        # Clear log, confirm filesize is 0 bytes
        clear_log()
        self.assertEqual(os.stat('app.log')[6], 0)

    @cpython_only
    def test_09_check_log_size(self):
        # Create mock log file with size 100001 bytes
        with open('app.log', 'wb') as f:
            f.write(os.urandom(100001))
        self.assertEqual(os.stat('app.log')[6], 100001)

        # Confirm no check_log_size timer in SoftwareTimer queue
        self.assertTrue("check_log_size" not in str(app_context.timer_instance.schedule))

        # Run function, confirm log deleted and re-created
        check_log_size()
        self.assertLessEqual(os.stat('app.log')[6], 100)

        # Confirm created check_log_size timer (runs every 60 seconds)
        asyncio.run(asyncio.sleep_ms(10))
        self.assertTrue("check_log_size" in str(app_context.timer_instance.schedule))
        app_context.timer_instance.cancel("check_log_size")

        # Simulate timer expiring while log size is 1kb
        with open('app.log', 'wb') as f:
            f.write(os.urandom(1000))
        self.assertEqual(os.stat('app.log')[6], 1000)
        check_log_size()
        # Confirm did not clear log (has not reached limit)
        self.assertEqual(os.stat('app.log')[6], 1000)
