#!/usr/bin/python3

import os
import sys
import time
import argparse
import unittest
from helper_functions import valid_ip


# Get absolute paths to mock_dir, repo root dir
client_tests_dir = os.path.dirname(os.path.realpath(__file__))
repo_dir = os.path.dirname(os.path.dirname(client_tests_dir))


def run_tests(ip):
    # Write test node IP to disk (read by unit tests)
    with open(os.path.join(client_tests_dir, 'CLIENT_TEST_TARGET_IP'), 'w') as file:
        file.write(ip)

    # Discover tests
    loader = unittest.TestLoader()
    start_dir = os.path.join(repo_dir, 'tests', 'client')
    suite = loader.discover(start_dir, pattern='client_test*.py')

    # Run tests, print each test name to console as they run
    # This helps identify broken test if connection hangs
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Remove target IP file
    os.remove(os.path.join(client_tests_dir, 'CLIENT_TEST_TARGET_IP'))

    # Exit non-zero if any tests failed
    if not result.wasSuccessful():
        sys.exit(1)


def upload_test_config(ip):
    # Import provisioner class, argparse.Namespace
    sys.path.insert(0, os.path.join(repo_dir, 'CLI'))
    from provision import Provisioner
    from argparse import Namespace

    # Instantiate with test config file + test node IP, wait 30 seconds for reboot to complete
    # Provisioner class starts upload automatically when instantiated with valid args
    config_file = open(os.path.join(client_tests_dir, 'client_test_config.json'), 'r')
    args = Namespace(config=config_file, ip=ip, node=None, all=None, test=None, password='password')
    Provisioner(args, '')
    time.sleep(30)


def parse_args():
    # Required IP arg, optional upload arg
    parser = argparse.ArgumentParser(description='Send exhuastive set of API commands to ESP32 test node.')
    parser.add_argument('--ip', type=validate_ip, required=True, help='Test node IP address')
    parser.add_argument('--upload', action='store_true', help='Upload test config')
    args = parser.parse_args()

    # Upload config to test node if called with --upload flag
    if args.upload:
        upload_test_config(args.ip)

    run_tests(args.ip)


def validate_ip(ip):
    if not valid_ip(ip):
        raise argparse.ArgumentTypeError(f"Invalid IP address '{ip}'")
    return ip


if __name__ == '__main__':
    parse_args()
