print("--------Booted--------")

import uasyncio as asyncio
import logging

# Set log file and syntax
logging.basicConfig(level=logging.DEBUG, filename='app.log', format='%(asctime)s - %(levelname)s - %(name)s - %(message)s', style='%')
log = logging.getLogger("Main")
log.info("Booted")



async def disk_monitor():
    import os

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
            await asyncio.sleep(1) # Prevents webrepl_cli.py from hanging after upload (esp reboots too fast)
            from Config import reboot
            reboot()

        # Don't let the log exceed 500 KB, full disk hangs system + can't pull log via webrepl
        elif os.stat('app.log')[6] > 100000:
            print("\nLog exceeded 100 KB, clearing...\n")

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



def check_sensor_conditions(group):
    # Store return value from each sensor in group
    conditions = []

    # Check conditions for all enabled sensors
    for sensor in group:
        if sensor.enabled:
            conditions.append(sensor.condition_met())

    return conditions



def determine_correct_action(conditions):
    # Determine action to apply to target devices: True = turn on, False = turn off, None = do nothing
    # Turn on: Requires only 1 sensor to return True
    # Turn off: ALL sensors to return False
    # Nothing: Requires 1 sensor to return None and 0 sensors returning True
    if True in conditions:
        action = True
    elif None in conditions:
        action = None
    else:
        action = False

    return action



def apply_action(group, action):
    # TODO consider re-introducing sensor.state - could then skip iterating devices if all states match action. Can also print "Motion detected" only when first detected
    # Issue: When device rules change, device's state is flipped to allow to take effect - this will not take effect if sensor.state blocks loop. Could change sensor.state?

    for device in group:
        # Do not turn device on/off if already on/off, or if device is disabled
        if device.enabled and not action == device.state:
            # int converts True to 1, False to 0
            success = device.send(int(action))

            # Only change device state if send returned True
            if success:
                device.state = action

                # When thermostat turns targets on/off, clear recent readings (used to detect failed on/off command) to prevent false positives
                for i in device.triggered_by:
                    if i.sensor_type == "si7021":
                        i.recent_temps = []



# Main loop - monitor sensors, apply actions if conditions met
async def main(config):
    while True:
        for group in config.groups:

            conditions = check_sensor_conditions(config.groups[group]["triggers"])

            await asyncio.sleep(0)

            action = determine_correct_action(conditions)

            await asyncio.sleep(0)

            if action == None:
                # Skip to next group if no action required
                continue
            else:
                # Otherwise apply actions
                apply_action(config.groups[group]["targets"], action)

        # Must be >0 to avoid blocking webrepl. Low values bottleneck webrepl speed, but this is acceptable since only used in maintenance
        await asyncio.sleep_ms(1)



if __name__ == "__main__":
    import webrepl
    import json
    from Config import Config
    from SoftwareTimer import timer
    from Api import app

    # Instantiate config object
    with open('config.json', 'r') as file:
        config = Config(json.load(file))

    gc.collect()

    webrepl.start()

    # Pass config object to API instance
    app.config = config

    # SoftwareTimer loop checks if timers have expired, applies actions
    asyncio.create_task(timer.loop())
    # Disk_monitor deletes log when size limit exceeded, reboots when new code upload received
    asyncio.create_task(disk_monitor())
    # Config loop rebuilds schedule rules when config_timer expires around 3am every day
    asyncio.create_task(config.loop())
    # Start API server, await requests
    asyncio.create_task(app.run())

    asyncio.run(main(config))
