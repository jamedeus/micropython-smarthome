# This file is executed on every boot (including wake-boot from deepsleep)
#import esp
#esp.osdebug(None)

print("--------Booted--------")

import webrepl
import time
import os
import uasyncio as asyncio
import logging
import Config
import Api

# Set log file and syntax
logging.basicConfig(level=logging.INFO, filename='app.log', format='%(asctime)s - %(levelname)s - %(name)s - %(message)s', style='%')
log = logging.getLogger("Main")
log.info("Booted")



async def disk_monitor():
    print("Disk Monitor Started\n")

    # Get filesize/modification time (to detect upload in future)
    old = os.stat("boot.py")

    while True:
        # Check if file changed on disk
        if not os.stat("boot.py") == old:
            # If file changed (new code received from webrepl), reboot
            print("\nReceived new code from webrepl, rebooting...\n")
            log.info("Received new code from webrepl, rebooting...")
            time.sleep(1) # Prevents webrepl_cli.py from hanging after upload (esp reboots too fast)
            Config.reboot()
        # Don't let the log exceed 500 KB, full disk hangs system + can't pull log via webrepl
        elif os.stat('app.log')[6] > 500000:
            print("\nLog exceeded 500 KB, clearing...\n")
            os.remove('log.txt')
            log.info("Deleted old log (exceeded 500 KB size limit)")
        else:
            await asyncio.sleep(1) # Only check once per second



async def main():
    # Check if desktop device configured, start desktop_integration (unless already running)
    for i in Config.config.devices:
        if i.device_type == "desktop" and not i.integration_running:
            log.info("Desktop integration is being used, creating asyncio task to listen for messages")
            asyncio.create_task(i.desktop_integration())
            i.integration_running = True

    # Create hardware interrupts + create async tasks for sensor loops
    for sensor in Config.config.sensors:
        if not sensor.loop_started:
            sensor.enable()

    # Start listening for API commands
    asyncio.create_task(Api.server.run())

    # Listen for new code upload (auto-reboot when updated), prevent log from filling disk
    asyncio.create_task(disk_monitor())

    # Keep running, all tasks stop if function exits
    while True:
        await asyncio.sleep(1)



gc.collect()

webrepl.start()

asyncio.run(main())
