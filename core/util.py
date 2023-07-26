import os
import json
import logging
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
