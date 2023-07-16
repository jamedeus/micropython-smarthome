#!/usr/bin/python3

import os
import sys
import time
import asyncio
import unittest
import coverage

# Add project files to python path
sys.path.insert(0, os.path.abspath('../core'))
sys.path.insert(0, os.path.abspath('../lib'))
sys.path.insert(0, os.path.abspath('../devices'))
sys.path.insert(0, os.path.abspath('../sensors'))

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


async def run_tests():
    cov = coverage.Coverage(source=['../core', '../devices', '../sensors'])
    cov.start()

    # Discover tests
    loader = unittest.TestLoader()
    start_dir = '.'
    suite = loader.discover(start_dir)

    # Run
    runner = unittest.TextTestRunner()
    runner.run(suite)

    # Print coverage report
    cov.stop()
    cov.save()
    cov.report(show_missing=True, precision=1)


asyncio.run(run_tests())
