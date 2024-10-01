#!/usr/bin/python3

import os
import sys
import time
import json
import shutil
import logging
import asyncio
import requests
import unittest
import subprocess
import nest_asyncio


# Get absolute paths to mock_dir, repo root dir
mock_dir = os.path.dirname(os.path.realpath(__file__))
repo_dir = os.path.dirname(os.path.dirname(mock_dir))


# Set up mocked environment used to run micropython code in cpython
def set_mocks():
    # Add project files to python path
    sys.path.insert(0, os.path.join(repo_dir, 'core'))
    sys.path.insert(0, os.path.join(repo_dir, 'lib'))
    sys.path.insert(0, os.path.join(repo_dir, 'lib', 'ir_codes'))
    sys.path.insert(0, os.path.join(repo_dir, 'devices'))
    sys.path.insert(0, os.path.join(repo_dir, 'sensors'))

    # Add mock modules to python path
    # Must be last to give mock libraries priority over ../lib
    sys.path.insert(0, os.path.join(mock_dir, 'mocks'))

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

    # Patch requests.Response.json to raise ValueError instead of JSONDecodeError
    import mock_requests
    requests.Response = mock_requests.MockResponse
    requests.sessions.Session.request = mock_requests.mock_request

    # Patch asyncio to add missing sleep methods
    import mock_asyncio
    asyncio.sleep_ms = mock_asyncio.sleep_ms
    asyncio.sleep_us = mock_asyncio.sleep_us

    # Patch time.time to return int epoch time (no subseconds)
    import mock_time
    time.time = mock_time.mock_time

    # Use unit_test_config.json as mock config, allows saving rules/keywords etc
    # Also contains IP and ports for mock_command_receiver container
    shutil.copy2(
        os.path.join(repo_dir, 'tests', 'firmware', 'unit_test_config.json'),
        'config.json'
    )

    # Create mock wifi_credentials.json (ESP32 nodes create this file when user
    # enters credentials during initial setup)
    with open('wifi_credentials.json', 'w') as file:
        json.dump({'ssid': 'mock_ssid', 'password': 'mock_password'}, file)

    # Build lib/hardware_classes.py (normally compiled into firmware)
    subprocess.run([
        'python3',
        os.path.join(repo_dir, 'lib', 'build_hardware_classes.py')
    ])

    # Build lib/ir_code_classes.py (normally compiled into firmware)
    subprocess.run([
        'python3',
        os.path.join(repo_dir, 'lib', 'build_ir_code_classes.py')
    ])


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
    start_dir = os.path.join(repo_dir, 'tests', 'firmware')
    suite = loader.discover(start_dir)

    # Run
    runner = unittest.TextTestRunner()
    result = runner.run(suite)

    # Remove mock files
    for i in [
        'config.json',
        'ir_macros.json',
        'wifi_credentials.json',
        'app.log',
        'webrepl_cfg.py'
    ]:
        try:
            os.remove(i)
        except FileNotFoundError:
            pass

    # Exit non-zero if any tests failed
    if not result.wasSuccessful():
        sys.exit(1)


if __name__ == '__main__':
    set_mocks()
    asyncio.run(run_tests())
