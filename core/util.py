import os
import time
import json
import logging
import SoftwareTimer

log = logging.getLogger("Util")


def is_device(string):
    '''Takes string, returns True if it begins with "device"'''
    try:
        return string.startswith("device")
    except AttributeError:
        return False


def is_sensor(string):
    '''Takes string, returns True if it begins with "sensor"'''
    try:
        return string.startswith("sensor")
    except AttributeError:
        return False


def is_device_or_sensor(string):
    '''Takes string, returns True if it begins with "device" or "sensor"'''
    try:
        return (string.startswith("device") or string.startswith("sensor"))
    except AttributeError:
        return False


def is_latitude(num):
    '''Takes number, returns True if between -90 and 90 (valid latitude)'''
    try:
        return -90 <= float(num) <= 90
    except ValueError:
        return False


def is_longitude(num):
    '''Takes number, returns True if between -180 and 180 (valid longitude)'''
    try:
        return -180 <= float(num) <= 180
    except ValueError:
        return False


def read_wifi_credentials_from_disk():
    '''Reads wifi_credentials.json from disk and returns as dict'''
    with open('wifi_credentials.json', 'r', encoding='utf-8') as file:
        return json.load(file)


def read_config_from_disk():
    '''Reads config.json from disk and returns as dict'''
    with open('config.json', 'r', encoding='utf-8') as file:
        return json.load(file)


def write_config_to_disk(conf):
    '''Takes config dict, writes to config.json on disk'''
    if not isinstance(conf, dict):
        return False
    with open('config.json', 'w', encoding='utf-8') as file:
        json.dump(conf, file)
    return True


def read_ir_macros_from_disk():
    '''Reads ir_macros.json from disk and returns as dict'''
    try:
        with open('ir_macros.json', 'r', encoding='utf-8') as file:
            return json.load(file)
    except OSError:
        return {}


def write_ir_macros_to_disk(conf):
    '''Takes IR macros dict, writes to ir_macros.json on disk'''
    if not isinstance(conf, dict):
        return False
    with open('ir_macros.json', 'w', encoding='utf-8') as file:
        json.dump(conf, file)
    return True


def reboot(*args):
    '''Writes log message and performs hard reboot. Accepts args to allow
    calling with hardware timer (passes self as arg).
    '''
    print_with_timestamp("Reboot function called, rebooting...")
    log.critical("Reboot function called, rebooting...\n")
    from machine import reset
    reset()


def clear_log():
    '''Deletes app.log from disk, creates blank log and new handler'''

    # Close file, remove
    logging.root.handlers[0].close()
    os.remove('app.log')

    # Create new handler, set format
    h = logging.FileHandler('app.log')
    h.setFormatter(logging.Formatter(
        '%(asctime)s - %(levelname)s - %(name)s - %(message)s'
    ))

    # Replace old handler with new
    logging.root.handlers.clear()
    logging.root.addHandler(h)


def check_log_size():
    '''Checks app.log size, deletes if larger than 100 KB.
    Called by SoftwareTimer every 60 seconds to keep log from filling disk.
    '''
    if os.stat('app.log')[6] > 100000:
        print_with_timestamp("\nLog exceeded 100 KB, clearing...\n")
        clear_log()
        log.critical("Deleted old log (exceeded 100 KB size limit)")

    # Add back to queue
    SoftwareTimer.timer.create(60000, check_log_size, "check_log_size")


def get_timestamp():
    '''Returns current timestamp with YYYY-MM-DD HH:MM:SS format'''
    ct = list(time.localtime())
    # Add leading 0 to single-digit month, day, hour, min, sec
    for i in range(1, 6):
        if len(str(ct[i])) == 1:
            ct[i] = "0" + str(ct[i])
    return "{0}-{1}-{2} {3}:{4}:{5}".format(*ct)


def print_with_timestamp(msg):
    '''Takes message, prints to console with prepended timestamp'''
    print(f"{get_timestamp()}: {msg}")
