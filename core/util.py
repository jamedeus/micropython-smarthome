import os
import json
import logging
import uasyncio as asyncio

log = logging.getLogger("Util")


def is_device(string):
    try:
        return string.startswith("device")
    except AttributeError:
        return False


def is_sensor(string):
    try:
        return string.startswith("sensor")
    except AttributeError:
        return False


def is_device_or_sensor(string):
    try:
        return (string.startswith("device") or string.startswith("sensor"))
    except AttributeError:
        return False


def read_config_from_disk():
    with open('config.json', 'r') as file:
        return json.load(file)


def write_config_to_disk(conf):
    if not isinstance(conf, dict):
        return False
    with open('config.json', 'w') as file:
        json.dump(conf, file)
    return True


# Must accept arg (hardware Timer passes self as arg)
def reboot(arg=None):
    print("Reboot function called, rebooting...")
    log.info("Reboot function called, rebooting...\n")
    from machine import reset
    reset()


def clear_log():
    # Close file, remove
    logging.root.handlers[0].close()
    os.remove('app.log')

    # Create new handler, set format
    h = logging.FileHandler('app.log')
    h.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(message)s'))

    # Replace old handler with new
    logging.root.handlers.clear()
    logging.root.addHandler(h)


# Coroutine that keeps log under size limit, reboots when new code uploaded
async def disk_monitor():
    print("Disk Monitor Started\n")
    log.debug("Disk Monitor Started")

    # Get filesize/modification time (to detect upload in future)
    if "main.py" in os.listdir():
        old = os.stat("main.py")
    else:
        # Exists in firmware, not filesystem
        old = None

    while True:
        # Check if file changed (or appeared) on disk
        if "main.py" in os.listdir() and os.stat("main.py") != old:
            print("\nReceived new code from webrepl, rebooting...\n")
            log.info("Received new code from webrepl, rebooting...")

            # Wait for webrepl connection to close before rebooting
            await asyncio.sleep(1)
            reboot()

        # Limit log to 100 KB (full disk causes hang, can't pull log via webrepl)
        elif os.stat('app.log')[6] > 100000:
            print("\nLog exceeded 100 KB, clearing...\n")
            clear_log()
            log.info("Deleted old log (exceeded 100 KB size limit)")

            # Allow logger to write new log file to disk before loop checks size again (crashes if doesn't exist yet)
            await asyncio.sleep(1)

        else:
            # Poll every 5 seconds
            await asyncio.sleep(1)
