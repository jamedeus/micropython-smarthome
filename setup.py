import os
import time
import json
import network
import webrepl
import machine
import uasyncio as asyncio

with open('config.json', 'r') as file:
    config = json.load(file)

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(config["wifi"]["ssid"], config["wifi"]["password"])
while not wlan.isconnected():
    continue

# Create directories
# Loop ensures all statements run, otherwise would fail to create tests if lib already exists
for directory in ['lib', 'lib/ir_tx', 'tests']:
    try:
        os.mkdir(directory)
    except OSError:
        pass

webrepl.start()

print("\nFinished setup - please upload final code\n")


async def disk_monitor():
    # Get filesize/modification time (to detect upload in future)
    old = os.stat("boot.py")

    while True:
        # Check if file changed on disk
        if not os.stat("boot.py") == old:
            # If file changed (new code received from webrepl), reboot
            print("\nReceived new code from webrepl, rebooting...\n")
            time.sleep(1)  # Prevents webrepl_cli.py from hanging after upload (esp reboots too fast)
            machine.reset()
        else:
            await asyncio.sleep(1)  # Only check once per second

# Await final code upload, reboot automatically when received
asyncio.run(disk_monitor())
