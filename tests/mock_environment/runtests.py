#!/usr/bin/python3

import os
import sys
import time
import json
import shutil
import logging
import asyncio
import unittest
import nest_asyncio


# Set up mocked environment used to run micropython code in cpython
def set_mocks():
    # Add project files to python path
    sys.path.insert(0, os.path.abspath('../../core'))
    sys.path.insert(0, os.path.abspath('../../lib'))
    sys.path.insert(0, os.path.abspath('../../devices'))
    sys.path.insert(0, os.path.abspath('../../sensors'))

    # Add mock modules to python path
    # Must be last to give mock libraries priority over ../lib
    sys.path.insert(0, os.path.abspath('mocks'))

    def sleep_us(us):
        # Convert microseconds to seconds
        time.sleep(us / 1000000.0)

    def sleep_ms(ms):
        # Convert milliseconds to seconds
        time.sleep(ms / 1000.0)

    # Add missing methods to time module
    time.sleep_us = sleep_us
    time.sleep_ms = sleep_ms

    # Allow calling asyncio.run when an event loop is already running
    # More closely approximates micropython uasyncio behavior
    nest_asyncio.apply()

    # Patch logging methods and attributes with mocks
    import mock_logging
    logging.Handler = mock_logging.Handler
    logging.Logger = mock_logging.Logger
    logging.basicConfig = mock_logging.basicConfig
    logging.getLogger = mock_logging.getLogger
    logging.FileHandler = mock_logging.FileHandler
    logging.root = mock_logging.Logger()
    logging.root.handlers = [mock_logging.Handler()]

    # Patch json.loads to raise OSError instead of JSONDecodeError
    import mock_json
    json.JSONDecoder = mock_json.MockDecoder
    json.loads = mock_json.mock_loads

    # Use unit_test_config.json as mock config.json, allow saving schedule rules, keywords, etc
    # Also contains IP and ports for mock_command_receiver container
    shutil.copy2(os.path.abspath('../firmware/unit_test_config.json'), 'config.json')


async def run_tests():
    # Add API backend to loop (receives commands from tests)
    from Api import app
    asyncio.create_task(app.run())
    asyncio.run(asyncio.sleep(0.5))

    # Add captive portal to loop (receives DNS queries from tests)
    from wifi_setup import run_captive_portal
    asyncio.create_task(run_captive_portal(port=8316))
    asyncio.run(asyncio.sleep(0.5))

    # Discover tests
    loader = unittest.TestLoader()
    start_dir = '../firmware/'
    suite = loader.discover(start_dir)

    # Run
    runner = unittest.TextTestRunner()
    result = runner.run(suite)

    # Remove mock files
    try:
        os.remove('config.json')
        os.remove('app.log')
    except FileNotFoundError:
        pass

    # Exit non-zero if any tests failed
    if not result.wasSuccessful():
        sys.exit(1)


if __name__ == '__main__':
    set_mocks()
    asyncio.run(run_tests())
