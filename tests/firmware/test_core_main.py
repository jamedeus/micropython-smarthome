import json
import webrepl
import unittest
from Api import app
from Config import Config
from main import start
from cpython_only import cpython_only

# Read wifi credentials from disk
with open('config.json', 'r') as file:
    test_config = json.load(file)


config_file = {
    "wifi": {
        "ssid": test_config["wifi"]["ssid"],
        "password": test_config["wifi"]["password"]
    },
    "metadata": {
        "id": "unit-testing",
        "location": "test environment",
        "floor": "0",
        "schedule_keywords": {}
    },
    "sensor1": {
        "targets": [
            "device2"
        ],
        "_type": "si7021",
        "schedule": {
            "10:00": 74,
            "22:00": 74
        },
        "default_rule": 74,
        "mode": "cool",
        "tolerance": 1,
        "nickname": "sensor1"
    },
    "sensor2": {
        "_type": "pir",
        "targets": [
            "device1"
        ],
        "pin": 16,
        "default_rule": 1,
        "schedule": {},
        "nickname": "sensor2"
    },
    "sensor3": {
        "_type": "pir",
        "targets": [
            "device1"
        ],
        "pin": 17,
        "default_rule": 1,
        "schedule": {},
        "nickname": "sensor3"
    },
    "device1": {
        "pin": 4,
        "_type": "pwm",
        "schedule": {
            "09:00": 734,
            "11:00": 345,
            "20:00": 915
        },
        "min_bright": 0,
        "max_bright": 1023,
        "default_rule": 512,
        "nickname": "device1"
    },
    "device2": {
        "pin": 18,
        "_type": "dumb-relay",
        "schedule": {
            "09:00": "enabled"
        },
        "default_rule": "enabled",
        "nickname": "device2"
    }
}


class TestMain(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Instantiate Config object, run all setup steps except API calls
        cls.config = Config(config_file, delay_setup=True)
        cls.config.instantiate_peripherals()
        cls.config.build_queue()
        cls.config.build_groups()

    @cpython_only
    def test_01_start(self):
        from unittest.mock import patch, MagicMock

        # Confirm webrepl not started
        self.assertEqual(webrepl.listen_s, None)

        # Mock Config init to return existing Config object
        # Mock asyncio.get_event_loop to return mock with methods that return immediately
        with patch('main.Config', return_value=self.config), \
             patch('main.asyncio.get_event_loop', return_value=MagicMock()) as mock_loop:
            mock_loop.create_task = MagicMock()
            mock_loop.run_forever = MagicMock()

            # Run function
            start()

        # Confirm API received correct config, webrepl started
        self.assertEqual(app.config, self.config)
        self.assertIsNotNone(webrepl.listen_s)
