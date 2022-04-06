import network, gc, upip, json

with open('config.json', 'r') as file:
    config = json.load(file)

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(config["wifi"]["ssid"], config["wifi"]["password"])
while not wlan.isconnected():
    continue

gc.collect()

print("\nInstalling dependencies...\n")

upip.install('picoweb')

import webrepl
webrepl.start()

print("\nFinished installing dependencies - please upload final code\n")

import uasyncio as asyncio

async def disk_monitor():
    import os, time, machine

    # Get filesize/modification time (to detect upload in future)
    old = os.stat("boot.py")

    while True:
        # Check if file changed on disk
        if not os.stat("boot.py") == old:
            # If file changed (new code received from webrepl), reboot
            print("\nReceived new code from webrepl, rebooting...\n")
            time.sleep(1) # Prevents webrepl_cli.py from hanging after upload (esp reboots too fast)
            machine.reset()
        else:
            await asyncio.sleep(1) # Only check once per second

# Await final code upload, reboot automatically when received
asyncio.run(disk_monitor())
