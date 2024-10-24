#!/usr/bin/env python3

import os
import sys
import time
import json
import argparse
import unittest
from helper_functions import valid_ip


# Get absolute paths to mock_dir, repo root dir
client_tests_dir = os.path.dirname(os.path.realpath(__file__))
repo_dir = os.path.dirname(os.path.dirname(client_tests_dir))


def run_tests(ip):
    # Write test node IP to disk (read by unit tests)
    test_node_ip_file = os.path.join(client_tests_dir, 'CLIENT_TEST_TARGET_IP')
    with open(test_node_ip_file, 'w', encoding='utf-8') as file:
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
    os.remove(test_node_ip_file)

    # Exit non-zero if any tests failed
    if not result.wasSuccessful():
        sys.exit(1)


def upload_test_config(ip):
    sys.path.insert(0, os.path.join(repo_dir, 'CLI'))
    from provision_tools import get_modules, provision

    # Read test config from disk
    config_path = os.path.join(client_tests_dir, 'client_test_config.json')
    with open(config_path, 'r', encoding='utf-8') as file:
        config = json.load(file)

    # Upload test config to node IP, wait 30 seconds for reboot to complete
    result = provision(
        ip=ip,
        password='password',
        config=config,
        modules=get_modules(config, repo_dir)
    )
    if result['status'] != 200:
        print(result['message'])
        raise SystemExit
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
