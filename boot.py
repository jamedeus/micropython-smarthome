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

            # Close file, remove
            logging.root.handlers[0].close()
            os.remove('app.log')

            # Create new handler, set format
            h = logging.FileHandler('app.log')
            h.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(message)s'))

            # Replace old handler with new
            logging.root.handlers.clear()
            logging.root.addHandler(h)

            log.info("Deleted old log (exceeded 500 KB size limit)")

            # Allow logger to write new log file to disk before loop checks size again (crashes if doesn't exist yet)
            await asyncio.sleep(1)
        else:
            await asyncio.sleep(1) # Only check once per second



# Main loop - monitor sensors, apply actions if conditions met
async def main():
    while True:
        for group in config.groups:

            # Store return value from each sensor in group
            conditions = []

            # Check conditions for all enabled sensors
            for sensor in config.groups[group]["triggers"]:
                if sensor.enabled:
                    conditions.append(sensor.condition_met())

            # Determine action to apply to target devices: True = turn on, False = turn off, None = do nothing
            # Turn on: Requires only 1 sensor to return True
            # Turn off: ALL sensors to return False
            # Nothing: Requires 1 sensor to return None and 0 sensors returning True
            if True in conditions:
                action = True
            elif None in conditions:
                # Skip to next group if no action required
                continue
            else:
                action = False

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

# Import + initialize API, pass config object
from Api import app
app.config = config

# Create main loop, add tasks
# TODO determine if SoftwareTimer.loop and Config.loop are running on this loop or different
# If different, remove call from their init methods and move it here
# TODO probably should move here regardless to keep in one place
loop = asyncio.get_event_loop()
loop.create_task(disk_monitor())
loop.create_task(main())
loop.create_task(app.run())

# Run
loop.run_forever()
