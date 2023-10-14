import os
import time
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


# Returns True if argument is valid latitude
def is_latitude(num):
    try:
        return -90 <= float(num) <= 90
    except ValueError:
        return False


# Returns True if argument is valid longitude
def is_longitude(num):
    try:
        return -180 <= float(num) <= 180
    except ValueError:
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
    print_with_timestamp("Reboot function called, rebooting...")
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
        print_with_timestamp("\nLog exceeded 100 KB, clearing...\n")
        clear_log()
        log.info("Deleted old log (exceeded 100 KB size limit)")

    # Add back to queue
    SoftwareTimer.timer.create(60000, check_log_size, "check_log_size")


# Returns current timestamp with YYYY-MM-DD HH:MM:SS format
def get_timestamp():
    ct = list(time.localtime())
    # Add leading 0 to single-digit month, day, hour, min, sec
    for i in range(1, 6):
        if len(str(ct[i])) == 1:
            ct[i] = "0" + str(ct[i])
    return "{0}-{1}-{2} {3}:{4}:{5}".format(*ct)


# Takes message, prints with prepended timestamp
def print_with_timestamp(msg):
    print(f"{get_timestamp()}: {msg}")
