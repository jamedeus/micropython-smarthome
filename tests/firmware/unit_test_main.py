import os
import gc
import sys
import json
import asyncio
import network
import logging
import unittest
import app_context

# Set level to prevent logging from slowing down tests, using memory, etc
logging.basicConfig(
    level=logging.CRITICAL,
    filename='app.log',
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
    style='%'
)
log = logging.getLogger("Main")

# Add tests to path
sys.path.insert(len(sys.path), '/tests')


def reboot():
    import machine
    machine.reset()


def start_webrepl():
    # Start webrepl to allow upload
    import webrepl
    connect_wifi()
    webrepl.start()

    print("\nPress enter to reboot when upload complete")
    input()
    print("Rebooting...")
    reboot()


def load_testing_config_file():
    try:
        with open('testing_config.json', 'r') as file:
            testing_config = json.load(file)
    except OSError:
        # Return template if config doesn't exist
        testing_config = {}
        testing_config["results"] = {}
        testing_config["results"]["core"] = {}
        testing_config["results"]["api"] = {}
        testing_config["results"]["device"] = {}
        testing_config["results"]["sensor"] = {}

    return testing_config


async def run_tests(testing_config, target):
    print(f"---RUNNING {target.upper()} TESTS---\n\n")

    runner = unittest.TestRunner()

    # Record total tests, failed, errored, and skipped for each test case
    detailed_results = {}

    # Iterate modules to find tests
    for test in os.listdir():
        # Only import tests if they are in correct category (core, device, sensor)
        if test.startswith("test_" + target):
            module = __import__(test.split(".")[0])
        else:
            continue

        # Find and run unittest.TestCase in module
        for i in dir(module):
            c = getattr(module, i)
            try:
                if issubclass(c, unittest.TestCase):
                    suite = unittest.TestSuite()
                    suite.addTest(c)
                    gc.collect()
                    result = runner.run(suite)

                    # Record results
                    detailed_results[test] = {}
                    detailed_results[test]["tests_run"] = result.testsRun
                    detailed_results[test]["failed"] = result.failuresNum
                    detailed_results[test]["errors"] = result.errorsNum

                    # Reduce mem fragmentation when running large number of tests
                    del suite
                    gc.collect()
            except TypeError:
                pass

    print("\n\n---TESTING COMPLETE---\n\n")

    print_report(detailed_results)

    print("Memory remaining:")
    import micropython
    micropython.mem_info()
    print()

    # Add results to report, write to disk
    testing_config["results"][target] = detailed_results
    with open('testing_config.json', 'w') as file:
        json.dump(testing_config, file)


def prompt():
    # Load config, records results from last boot
    testing_config = load_testing_config_file()

    while True:
        print("\nWhat would you like to do?")
        print(" [1] Run core tests")
        print(" [2] Run api tests")
        print(" [3] Run device tests")
        print(" [4] Run sensor tests")
        print(" [5] View results from all tests")
        print(" [6] Start webrepl (wait for upload)")
        print(" [7] Reboot")
        choice = input()
        print()

        if choice == "1":
            asyncio.run(run_tests(testing_config, "core"))

        if choice == "2":
            asyncio.run(run_tests(testing_config, "api"))
            reboot()

        elif choice == "3":
            asyncio.run(run_tests(testing_config, "device"))
            reboot()

        elif choice == "4":
            asyncio.run(run_tests(testing_config, "sensor"))
            reboot()

        elif choice == "5":
            for category in testing_config["results"]:
                print(f"---{category.upper()} TESTS---\n")
                print_report(testing_config["results"][category])

        elif choice == "6":
            start_webrepl()

        elif choice == "7":
            reboot()

        else:
            print("\nERROR: Please enter a number and press enter.\n")


def print_report(results):
    total_tests = 0
    total_failed = 0

    # Print results summary
    for i in results:
        print(i.split(".")[0].split("_")[2])
        print(f" - Tests:         {results[i]['tests_run']}")
        print(f"   - Failed:      {results[i]['failed']}")
        print(f"   - Errored:     {results[i]['errors']}\n")
        total_tests += results[i]["tests_run"]
        total_failed += results[i]["failed"]

    print(f"Total:  {total_tests}\nFailed: {total_failed}\n")


def connect_wifi():
    wlan = network.WLAN()
    wlan.active(True)
    if not wlan.isconnected():
        with open('wifi_credentials.json', 'r') as file:
            credentials = json.load(file)
        wlan.connect(credentials["ssid"], credentials["password"])

    # Wait until connected
    while not wlan.isconnected():
        continue


def start():
    # Connect to wifi
    connect_wifi()

    # Import + initialize SoftwareTimer, add to shared context, add to async loop
    from SoftwareTimer import SoftwareTimer
    app_context.timer_instance = SoftwareTimer()
    asyncio.create_task(app_context.timer_instance.loop())

    # Import + initialize API, add to shared context, add to async loop
    from Api import Api
    app_context.api_instance = Api()
    asyncio.create_task(app_context.api_instance._run())

    gc.collect()

    prompt()
