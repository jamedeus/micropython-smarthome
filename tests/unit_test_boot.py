import os
import sys
import gc
import uasyncio as asyncio
import logging
import json
import network

# Set level to prevent logging from slowing down tests, using memory, etc
logging.basicConfig(level=logging.CRITICAL, filename='app.log', format='%(asctime)s - %(levelname)s - %(name)s - %(message)s', style='%')
log = logging.getLogger("Main")

# Add tests to path
sys.path.insert(len(sys.path), '/tests')



async def run_tests():
    print("\n\n---BEGIN TESTING---\n\n")

    # Load config, records results from last boot + which test to run on next boot
    try:
        with open('testing_config.json', 'r') as file:
            testing_config = json.load(file)
    except OSError:
        # If config doesn't exist, create template
        testing_config = {}
        testing_config["next"] = "module"
        testing_config["results"] = {}
        testing_config["results"]["module"] = {}
        testing_config["results"]["core"] = {}

    target = testing_config["next"]

    print(f"---RUNNING {target.upper()} TESTS---\n\n")

    runner = unittest.TestRunner()

    # Record total tests, failed, errored, and skipped for each test case
    detailed_results = {}

    # Import all modules under /tests
    for test in os.listdir('tests'):
        # Only run tests if they are in correct category (module or core)
        if test.startswith("test_" + target):
            module = __import__(test.split(".")[0])
        else:
            continue

        # Find and run test case classes in module
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
                    detailed_results[test]["skipped"] = result.skippedNum

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

    # Set test to run on next boot, add results to report
    if testing_config["next"] == "module":
        testing_config["next"] = "core"
        testing_config["results"]["module"] = detailed_results
    elif testing_config["next"] == "core":
        testing_config["next"] = "module"
        testing_config["results"]["core"] = detailed_results

    # Write to disk
    with open('testing_config.json', 'w') as file:
        json.dump(testing_config, file)

    # Start webrepl to allow upload
    import webrepl
    webrepl.start()

    while True:
        print("\nWhat would you like to do next?")
        print(" [1] Run module tests")
        print(" [2] Run core tests")
        print(f" [3] View results from current test ({target})")
        print(" [4] View results from last test")
        print(" [5] Reboot on upload")
        choice = input()
        print()

        if choice == "1":
            testing_config["next"] = "module"
            with open('testing_config.json', 'w') as file:
                json.dump(testing_config, file)
            import machine
            machine.reset()

        elif choice == "2":
            testing_config["next"] = "core"
            with open('testing_config.json', 'w') as file:
                json.dump(testing_config, file)
            import machine
            machine.reset()

        elif choice == "3":
            print_report(testing_config["results"][target])

        elif choice == "4":
            if target == "core":
                print_report(testing_config["results"]["module"])
            elif target == "module":
                print_report(testing_config["results"]["core"])

        elif choice == "5":
            loop = asyncio.new_event_loop()
            loop.create_task(disk_monitor())
            loop.run_forever()

        else:
            print("\nERROR: Please enter a number and press enter.\n")



def print_report(results):
    total_tests = 0
    total_failed = 0

    # Print results summary
    for i in results:
        print(i.split(".")[0].split("_")[2])
        print(f" - Tests:         {results[i]["tests_run"]}")
        print(f"   - Failed:      {results[i]["failed"]}")
        print(f"   - Errored:     {results[i]["errors"]}")
        print(f"   - Skipped:     {results[i]["skipped"]}\n")
        total_tests += results[i]["tests_run"]
        total_failed += results[i]["failed"]

    print(f"Total:  {total_tests}\nFailed: {total_failed}\n")



async def disk_monitor():
    from machine import reset
    # Get filesize/modification time (to detect upload in future)
    old = os.stat("boot.py")

    print("Waiting for new code...")

    while True:
        # Reboot if file changed on disk
        if not os.stat("boot.py") == old:
            await asyncio.sleep(1) # Prevents webrepl_cli.py from hanging after upload (esp reboots too fast)
            reset()
        else:
            await asyncio.sleep(1) # Only check once per second



if __name__ == "__main__":
    # Connect to wifi
    wlan = network.WLAN()
    wlan.active(True)
    if not wlan.isconnected():
        import json
        with open('config.json', 'r') as file:
            config = json.load(file)
        wlan.connect(config["wifi"]["ssid"], config["wifi"]["password"])

    # Wait until connected
    while not wlan.isconnected():
        continue

    try:
        import unittest
    except ImportError:
        # If not found, install and reboot
        import upip, machine
        upip.install("unittest")
        machine.reset()


    # Import SoftwareTimer instance, add to async loop
    from SoftwareTimer import timer
    asyncio.create_task(timer.loop())

    # Import + initialize API
    from Api import app
    asyncio.create_task(app.run())

    gc.collect()

    asyncio.run(run_tests())
