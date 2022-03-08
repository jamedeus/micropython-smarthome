# This file is executed on every boot (including wake-boot from deepsleep)
#import esp
#esp.osdebug(None)

import webrepl
import network
import time
from machine import Pin, Timer, RTC
import urequests
import json
import os
from random import randrange
import uasyncio as asyncio
import logging
import Config
import Api

print("--------Booted--------")

# Set log file and syntax
logging.basicConfig(level=logging.INFO, filename='app.log', format='%(asctime)s - %(levelname)s - %(name)s - %(message)s', style='%')
log = logging.getLogger("Main")
log.info("Booted")

# Hardware timer used to keep lights on for 5 min
timer = Timer(0)
# Timer re-runs startup every day at 3:00 am (reload schedule rules, sunrise/sunset times, etc)
config_timer = Timer(1)
# Used to reboot if startup hangs for longer than 1 minute
reboot_timer = Timer(2)
# Used when it is time to switch to the next schedule rule
next_rule_timer = Timer(3)

# Timer sets this to True at 3:00 am, causes main loop to reload config
reload_config = False

# Turn onboard LED on, indicates setup in progress
led = Pin(2, Pin.OUT, value=1)



# Called by timer every day at 3 am, regenerate timestamps for next day (epoch time)
def reload_schedule_rules(timer):
    print("3:00 am callback, reloading schedule rules...")
    log.info("3:00 am callback, reloading schedule rules...")
    # Temporary fix: Unable to reload after 2-3 days due to mem fragmentation (no continuous free block long enough for API response)
    # Since this will take a lot of testing to figure out, just reboot until then. TODO - fix memory issue
    reboot()



def reboot(arg="unused"):
    print("Reboot function called, rebooting...")
    log.info("Reboot function called, rebooting...\n")
    import machine
    machine.reset()



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
            reboot()
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
        if i.device == "desktop" and not i.integration_running:
            log.info("Desktop integration is being used, creating asyncio task to listen for messages")
            asyncio.create_task(i.desktop_integration())
            i.integration_running = True

    # Create hardware interrupts + create async task for sensor loops
    for sensor in Config.config.sensors:
        if not sensor.loop_started:
            sensor.enable()

    # Start listening for remote commands
    asyncio.create_task(Api.server.run())

    # Listen for new code upload (auto-reboot when updated), prevent log from filling disk
    asyncio.create_task(disk_monitor())

    # Keep running, all tasks stop if function exits
    while True:
        await asyncio.sleep(1)



gc.collect()

webrepl.start()

asyncio.run(main())
