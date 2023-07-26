import os
import json
import logging
import uasyncio as asyncio
import SoftwareTimer

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


# Checks log size and deletes when 100 KB exceeded
# Called by SoftwareTimer every 60 seconds
def check_log_size():
    if os.stat('app.log')[6] > 100000:
        print("\nLog exceeded 100 KB, clearing...\n")
        clear_log()
        log.info("Deleted old log (exceeded 100 KB size limit)")

    # Add back to queue
    SoftwareTimer.timer.create(60000, check_log_size, "check_log_size")


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
            reboot

        else:
            # Poll every 5 seconds
            await asyncio.sleep(1)
