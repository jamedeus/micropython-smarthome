import unittest
import os
import sys
import gc

# Add tests to path
sys.path.insert(len(sys.path), '/tests')

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

print("\n\n---BEGIN TESTING---\n\n")

gc.collect()
runner = unittest.TestRunner()
result = runner.run(suite)
gc.collect()

print("\n\n---TESTING COMPLETE---\n\n")



# After testing: listen for upload, reboot when new code received
import network, webrepl, machine
import uasyncio as asyncio

async def disk_monitor():
    # Get filesize/modification time (to detect upload in future)
    old = os.stat("boot.py")

    while True:
        # Reboot if file changed on disk
        if not os.stat("boot.py") == old:
            await asyncio.sleep(1) # Prevents webrepl_cli.py from hanging after upload (esp reboots too fast)
            machine.reset()
        else:
            await asyncio.sleep(1) # Only check once per second

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

# Create main loop, add tasks
loop = asyncio.get_event_loop()
# Disk_monitor reboots when new code upload received
loop.create_task(disk_monitor())

# Run
loop.run_forever()
