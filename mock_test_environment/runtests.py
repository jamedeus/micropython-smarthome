#!/usr/bin/python3

import os
import sys
import time
import asyncio
import unittest
import coverage

# Add mock modules to python path
sys.path.insert(0, os.path.abspath('mocks'))


# Add missing time.sleep_us method
def sleep_us(us):
    # Convert microseconds to seconds
    time.sleep(us / 1000000.0)
time.sleep_us = sleep_us


async def run_tests():
    cov = coverage.Coverage(source=['.'], omit=['/usr/*', 'test_*.py', 'runtests.py', 'mocks/*'])
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
    cov.report(show_missing=True)


asyncio.run(run_tests())
