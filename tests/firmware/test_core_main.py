import sys
import asyncio
import webrepl
import unittest
import app_context
from Config import Config
from cpython_only import cpython_only
from default_config import default_config

if sys.implementation.name == 'cpython':
    from main import start, async_exception_handler
    from unittest.mock import patch, MagicMock

config_file = {
    "metadata": {
        "id": "unit-testing",
        "location": "test environment",
        "floor": "0"
    },
    "schedule_keywords": {}
}


class TestMain(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Instantiate Config object, run all setup steps except API calls
        cls.config = Config(config_file, delay_setup=True)
        cls.config._instantiate_peripherals()
        cls.config._build_queue()
        cls.config._build_groups()

    @cpython_only
    def test_01_start(self):
        # Confirm webrepl not started
        self.assertEqual(webrepl.listen_s, None)

        # Mock Config init to return existing Config object
        # Mock SoftwareTimer init to return existing SoftwareTimer instance
        # Mock asyncio.get_event_loop to return mock with methods that return immediately
        with patch('main.Config', return_value=self.config), \
             patch('main.SoftwareTimer', return_value=app_context.timer_instance), \
             patch('main.asyncio.get_event_loop', return_value=MagicMock()) as mock_loop:
            mock_loop.create_task = MagicMock()
            mock_loop.run_forever = MagicMock()

            # Run function
            start()

        # Confirm shared context module contains correct config instance
        self.assertEqual(app_context.config_instance, self.config)
        # Confirm webrepl started
        self.assertIsNotNone(webrepl.listen_s)

    @cpython_only
    def test_02_start_default_config(self):
        # Mock Config init to return existing Config object
        # Mock SoftwareTimer init to return existing SoftwareTimer instance
        # Mock read_config_from_disk to raise OSError (simulate no config.json)
        # Mock asyncio.get_event_loop to return mock with methods that return immediately
        with patch('main.Config', return_value=self.config) as mock_config_class, \
             patch('main.SoftwareTimer', return_value=app_context.timer_instance), \
             patch('main.read_config_from_disk', side_effect=OSError), \
             patch('main.asyncio.get_event_loop', return_value=MagicMock()) as mock_loop:
            mock_loop.create_task = MagicMock()
            mock_loop.run_forever = MagicMock()

            # Run function
            start()

        # Confirm Config was instantiated with default config template
        mock_config_class.assert_called_once_with(default_config)

    @cpython_only
    def test_03_async_exception_handler(self):
        async def raise_exception():
            raise Exception('Uncaught exception')

        with patch('main.log.error') as mock_log_error:
            # Create new loop to avoid interference, add exception handler
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.set_exception_handler(async_exception_handler)

            # Create task that raises exception, let loop run
            loop.create_task(raise_exception())
            loop.run_until_complete(asyncio.sleep(0))

            # Confirm the uncaught exception was logged
            mock_log_error.assert_called()
            self.assertIn(
                "Exception('Uncaught exception')",
                str(mock_log_error.call_args_list[0][0][1])
            )

            loop.close()
