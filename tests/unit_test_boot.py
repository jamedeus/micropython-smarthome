import unittest
import os
import sys
import gc
import uasyncio as asyncio

# Add tests to path
sys.path.insert(len(sys.path), '/tests')



def find_tests():
    # Create empty test suite
    suite = unittest.TestSuite()

    # Import all modules under /tests
    for test in os.listdir('tests'):
        module = __import__(test.split(".")[0])

        # Find all classes in module, add to test suite
        for i in dir(module):
            c = getattr(module, i)
            try:
                if issubclass(c, unittest.TestCase):
                    suite.addTest(c)

            except TypeError:
                pass

    return suite



async def run_tests(suite):
    print("\n\n---BEGIN TESTING---\n\n")

    gc.collect()
    runner = unittest.TestRunner()
    result = runner.run(suite)
    gc.collect()

    print("\n\n---TESTING COMPLETE---\n\n")

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



# Get test suite containing all modules from /tests/ directory
suite = find_tests()

gc.collect()

# Import + initialize API
#from Api import app

# Import SoftwareTimer instance, add to async loop below
from SoftwareTimer import timer

# Create main loop, add tasks
loop = asyncio.get_event_loop()

# SoftwareTimer loop checks if timers have expired, applies actions
loop.create_task(timer.loop())
# Start API server, await requests
#loop.create_task(app.run())

# Add test runner last, ensure SoftwareTimer and API are ready for testing
loop.create_task(run_tests(suite))

gc.collect()

# Run
loop.run_forever()
