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
    "metadata": {
        "id": "unit-testing",
        "location": "test environment",
        "floor": "0",
        "schedule_keywords": {}
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
