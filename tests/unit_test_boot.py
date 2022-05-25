import unittest
import os
import sys
import gc
import uasyncio as asyncio

# Add tests to path
sys.path.insert(len(sys.path), '/tests')



async def run_tests():
    print("\n\n---BEGIN TESTING---\n\n")

    runner = unittest.TestRunner()

    # Record total tests, failed, errored, and skipped for each test case
    detailed_results = {}

    # Import all modules under /tests
    for test in os.listdir('tests'):
        module = __import__(test.split(".")[0])

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

    total_tests = 0
    total_failed = 0

    # Print results summary
    for i in detailed_results:
        print(i.split(".")[0].split("_")[1])
        print(f" - Tests:         {detailed_results[i]["tests_run"]}")
        print(f"   - Failed:      {detailed_results[i]["failed"]}")
        print(f"   - Errored:     {detailed_results[i]["errors"]}")
        print(f"   - Skipped:     {detailed_results[i]["skipped"]}\n")
        total_tests += detailed_results[i]["tests_run"]
        total_failed += detailed_results[i]["failed"]

    print(f"Total:  {total_tests}\nFailed: {total_failed}\n")

    print("Memory remaining:")
    import micropython
    micropython.mem_info()
    print("\n\n")

    asyncio.create_task(post_test())



async def post_test():
    # After testing: listen for upload, reboot when new code received
    import network, webrepl

    # Connect to wifi
    wlan = network.WLAN()
    wlan.active(True)
    if not wlan.isconnected():
        import json
        with open('config.json', 'r') as file:
            config = json.load(file)
        wlan.connect(config["wifi"]["ssid"], config["wifi"]["password"])

    # Wait until connected before starting webrepl
    while not wlan.isconnected():
        continue
    else:
        webrepl.start()

    asyncio.create_task(disk_monitor())



async def disk_monitor():
    from machine import reset
    # Get filesize/modification time (to detect upload in future)
    old = os.stat("boot.py")

    while True:
        # Reboot if file changed on disk
        if not os.stat("boot.py") == old:
            await asyncio.sleep(1) # Prevents webrepl_cli.py from hanging after upload (esp reboots too fast)
            reset()
        else:
            await asyncio.sleep(1) # Only check once per second



# Import + initialize API
from Api import app

# Import SoftwareTimer instance, add to async loop below
from SoftwareTimer import timer

# Create main loop, add tasks
loop = asyncio.get_event_loop()

# SoftwareTimer loop checks if timers have expired, applies actions
loop.create_task(timer.loop())
# Start API server, await requests
loop.create_task(app.run())

# Add test runner last, ensure SoftwareTimer and API are ready for testing
loop.create_task(run_tests())

gc.collect()

# Run
loop.run_forever()
