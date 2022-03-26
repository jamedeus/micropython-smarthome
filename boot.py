# This file is executed on every boot (including wake-boot from deepsleep)
#import esp
#esp.osdebug(None)

print("--------Booted--------")

import webrepl
import time
import os
import json
import uasyncio as asyncio
import logging
from Config import Config, reboot
from Api import Api

# Set log file and syntax
logging.basicConfig(level=logging.DEBUG, filename='app.log', format='%(asctime)s - %(levelname)s - %(name)s - %(message)s', style='%')
log = logging.getLogger("Main")
log.info("Booted")



async def disk_monitor():
    print("Disk Monitor Started\n")
    log.debug("Disk Monitor Started")

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
            os.remove('app.log')
            log.info("Deleted old log (exceeded 500 KB size limit)")
        else:
            await asyncio.sleep(1) # Only check once per second



async def main():
    # Check if desktop device configured, start desktop_integration (unless already running)
    for i in config.devices:
        if i.device_type == "desktop" and not i.integration_running:
            log.info("Desktop integration is being used, creating asyncio task to listen for messages")
            asyncio.create_task(i.desktop_integration())
            i.integration_running = True

    # Create hardware interrupts + create async tasks for sensor loops
    for sensor in config.sensors:
        if not sensor.loop_started:
            sensor.enable()
            log.debug(f"Enabled {sensor.name}")

    # Start listening for API commands
    server = Api(config)
    asyncio.create_task(server.run())

    # Listen for new code upload (auto-reboot when updated), prevent log from filling disk
    asyncio.create_task(disk_monitor())

    # Main loop - monitor sensors, apply actions if conditions met
    while True:
        for group in config.groups:

            # Default is turn off - overridden if condition is met for 1 or more trigger in group
            action = False

            # Check if conditions are met, excluding disabled sensors
            for sensor in config.groups[group]["triggers"]:
                if sensor.enabled and sensor.condition_met:
                    action = True
                    break # Only need 1 condition to be met

            # TODO consider re-introducing sensor.state - could then skip iterating devices if all states match action. Can also print "Motion detected" only when first detected
            # Issue: When device rules change, device's state is flipped to allow to take effect - this will not take effect if sensor.state blocks loop. Could change sensor.state?

            # Apply action (turn targets on/off)
            for device in config.groups[group]["targets"]:
                # Do not turn device on/off if already on/off
                if not action == device.state:
                    # int converts True to 1, False to 0
                    success = device.send(int(action))

                    # Only change device state if send returned True
                    if success:
                        device.state = action

        await asyncio.sleep_ms(20)



# Instantiate config object
with open('config.json', 'r') as file:
    config = Config(json.load(file))

gc.collect()

webrepl.start()

asyncio.run(main())
