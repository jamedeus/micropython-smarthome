import json
import os
import uasyncio as asyncio
import logging
import gc
import SoftwareTimer
import re
from functools import wraps
from uasyncio import Lock
from util import (
    is_device,
    is_sensor,
    is_device_or_sensor,
    reboot,
    read_config_from_disk,
    write_config_to_disk
)

# Set name for module's log lines
log = logging.getLogger("API")

lock = Lock()

# Matches HH:MM
timestamp_regex = r'^([0-1][0-9]|2[0-3]):[0-5][0-9]$'


# Ensure API call complete, connection closed before rebooting (reboot endpoint)
async def reboot_task():
    await lock.acquire()
    reboot()


class Api:
    def __init__(self, host='0.0.0.0', port=8123, backlog=5, timeout=20):
        self.host = host
        self.port = port
        self.backlog = backlog
        self.timeout = timeout

        # Populated by decorators + self.route
        # Key = endpoint, value = function
        self.url_map = {}

    # Decorator used to populate url_map
    def route(self, url):
        def _route(func):
            self.url_map[url] = func
        return _route

    # Decorator factory - takes number of required args (int), returns function with wrapper
    # that returns error if called with too few args
    def required_args(self, num):
        def decorator(func):
            @wraps(func)
            def wrapper(args):
                if len(args) < num:
                    return {"ERROR": "Invalid syntax"}
                return func(args)
            return wrapper
        return decorator

    # Decorator used to fetch device/sensor instance specified in first arg
    # Passes instance to wrapped function as first arg (or returns error if not found)
    # Should be placed after @required_args
    def get_target_instance(self, func):
        @wraps(func)
        def wrapper(args):
            target = self.config.find(args[0])
            if not target:
                return {"ERROR": "Instance not found, use status to see options"}
            return func(target, args[1:])
        return wrapper

    async def run(self):
        self.server = await asyncio.start_server(self.run_client, self.host, self.port, self.backlog)
        print('API: Awaiting client connection.\n')
        log.info("API ready")
        while True:
            await asyncio.sleep(25)

    async def run_client(self, sreader, swriter):
        try:
            # Read client request
            req = await asyncio.wait_for(sreader.readline(), self.timeout)

            # Receives null when client closes write stream - break and close read stream
            if not req:
                raise OSError

            # Determine if request is HTTP (browser) or raw JSON (much faster, used by api_client.py and other nodes)
            if req.startswith("GET"):
                # Received something like "GET /status HTTP/1.1"
                http = True

                req = req.decode()

                # Drop all except "/status"
                path = req.split()[1]

                # Convert to list, path ("/status") as first index, query string (if present) as second
                path = path.split("?", 1)

                if len(path) > 1:
                    # If query string present, split all parameters into args list
                    args = path[1]
                    args = args.split("/")
                else:
                    # No query string
                    args = ""

                # Drop all except path ("/status"), remove leading "/"
                path = path[0][1:]

                # Skip headers
                while True:
                    l = await asyncio.wait_for(sreader.readline(), self.timeout)
                    # Sequence indicates end of headers
                    if l == b"\r\n":
                        break

            else:
                # Received serialized json, no headers etc
                http = False

                # Convert to dict, get path and args
                data = json.loads(req)
                path = data[0]
                args = data[1:]

            # Acquire lock, prevents reboot until finished sending reply
            await lock.acquire()

            # Find endpoint matching path, call handler function and pass args
            try:
                # Call handler, receive reply for client
                reply = self.url_map[path](args)
            except KeyError:
                if http:
                    # Send headers before reply
                    swriter.write("HTTP/1.0 404 NA\r\nContent-Type: application/json\r\n\r\n")
                    swriter.write(json.dumps({"ERROR": "Invalid command"}).encode())
                else:
                    # Exit with error if no match found
                    swriter.write(json.dumps({"ERROR": "Invalid command"}))

                await swriter.drain()
                raise OSError

            if http:
                # Send headers before reply
                swriter.write("HTTP/1.0 200 NA\r\nContent-Type: application/json\r\n\r\n")
                swriter.write(json.dumps(reply).encode())
            else:
                # Send reply to client
                swriter.write(json.dumps(reply))

            await swriter.drain()

            # Prevent running out of mem after repeated requests
            gc.collect()

        except OSError:
            pass
        except asyncio.TimeoutError:
            pass
        # Client disconnected, close socket
        await sreader.wait_closed()

        # Allow reboot (if reboot endpoint was called)
        try:
            lock.release()
        except RuntimeError:
            # Prevent crash if connection timed out before lock acquired
            pass


app = Api()


@app.route("reboot")
def index(args):
    asyncio.create_task(reboot_task())
    return "Rebooting"


@app.route("status")
def status(args):
    return app.config.get_status()


@app.route("enable")
@app.required_args(1)
@app.get_target_instance
def enable(target, args):
    target.enable()
    return {"Enabled": target.name}


@app.route("enable_in")
@app.required_args(2)
@app.get_target_instance
def enable_for(target, args):
    period = float(args[0]) * 60000
    SoftwareTimer.timer.create(period, target.enable, "API")
    return {"Enabled": target.name, "Enable_in_seconds": period / 1000}


@app.route("disable")
@app.required_args(1)
@app.get_target_instance
def disable(target, args):
    target.disable()
    return {"Disabled": target.name}


@app.route("disable_in")
@app.required_args(2)
@app.get_target_instance
def disable_for(target, args):
    period = float(args[0]) * 60000
    SoftwareTimer.timer.create(period, target.disable, "API")
    return {"Disabled": target.name, "Disable_in_seconds": period / 1000}


@app.route("set_rule")
@app.required_args(2)
@app.get_target_instance
def set_rule(target, args):
    rule = args[0]

    # Replace url-encoded forward slashes (fade rules)
    if "%2F" in rule:
        rule = rule.replace("%2F", "/")

    if target.set_rule(rule):
        return {target.name: rule}
    else:
        return {"ERROR": "Invalid rule"}


@app.route("increment_rule")
@app.required_args(2)
@app.get_target_instance
def increment_rule(target, args):
    if "increment_rule" not in dir(target):
        return {"ERROR": "Unsupported target, must accept int or float rule"}

    if target.increment_rule(args[0]):
        return {target.name: target.current_rule}
    else:
        return {"ERROR": "Invalid rule"}


@app.route("reset_rule")
@app.required_args(1)
@app.get_target_instance
def reset_rule(target, args):
    target.set_rule(target.scheduled_rule)
    return {target.name: "Reverted to scheduled rule", "current_rule": target.current_rule}


@app.route("reset_all_rules")
def reset_all_rules(args):
    response = {}
    response["New rules"] = {}

    for device in app.config.devices:
        device.set_rule(device.scheduled_rule)
        response["New rules"][device.name] = device.current_rule

    for sensor in app.config.sensors:
        sensor.set_rule(sensor.scheduled_rule)
        response["New rules"][sensor.name] = sensor.current_rule

    return response


@app.route("get_schedule_rules")
@app.required_args(1)
@app.get_target_instance
def get_schedule_rules(target, args):
    return app.config.schedule[target.name]


@app.route("add_schedule_rule")
@app.required_args(3)
@app.get_target_instance
def add_schedule_rule(target, args):
    rules = app.config.schedule[target.name]

    if re.match(timestamp_regex, args[0]):
        timestamp = args[0]
    elif args[0] in app.config.schedule_keywords.keys():
        timestamp = args[0]
    else:
        return {"ERROR": "Timestamp format must be HH:MM (no AM/PM) or schedule keyword"}

    valid = target.rule_validator(args[1])

    if str(valid) == "False":
        return {"ERROR": "Invalid rule"}

    if timestamp in rules and (not len(args) >= 3 or not args[2] == "overwrite"):
        return {"ERROR": f"Rule already exists at {timestamp}, add 'overwrite' arg to replace"}
    else:
        rules[timestamp] = valid
        app.config.schedule[target.name] = rules
        # Schedule queue rebuild after connection closes (blocks for several seconds)
        SoftwareTimer.timer.create(1200, app.config.build_queue, "rebuild_queue")
        return {"Rule added": valid, "time": timestamp}


@app.route("remove_rule")
@app.required_args(2)
@app.get_target_instance
def remove_rule(target, args):
    rules = app.config.schedule[target.name]

    if re.match(timestamp_regex, args[0]):
        timestamp = args[0]
    elif args[0] in app.config.schedule_keywords.keys():
        timestamp = args[0]
    else:
        return {"ERROR": "Timestamp format must be HH:MM (no AM/PM) or schedule keyword"}

    try:
        del rules[timestamp]
        app.config.schedule[target.name] = rules
        # Schedule queue rebuild after connection closes (blocks for several seconds)
        SoftwareTimer.timer.create(1200, app.config.build_queue, "rebuild_queue")
    except KeyError:
        return {"ERROR": "No rule exists at that time"}

    return {"Deleted": timestamp}


@app.route("save_rules")
def save_rules(args):
    config = read_config_from_disk()

    for i in config:
        if is_device_or_sensor(i) and i in app.config.schedule:
            config[i]["schedule"] = app.config.schedule[i]

    write_config_to_disk(config)
    return {"Success": "Rules written to disk"}


@app.route("get_schedule_keywords")
def get_schedule_keywords(args):
    return app.config.schedule_keywords


@app.route("add_schedule_keyword")
@app.required_args(1)
def add_schedule_keyword(args):
    if not isinstance(args[0], dict):
        return {"ERROR": "Requires dict with keyword and timestamp"}

    keyword, timestamp = args[0].popitem()

    if re.match(timestamp_regex, timestamp):
        app.config.schedule_keywords[keyword] = timestamp
        # Schedule queue rebuild after connection closes (blocks for several seconds)
        SoftwareTimer.timer.create(1200, app.config.build_queue, "rebuild_queue")
        return {"Keyword added": keyword, "time": timestamp}
    else:
        return {"ERROR": "Timestamp format must be HH:MM (no AM/PM)"}


@app.route("remove_schedule_keyword")
@app.required_args(1)
def remove_schedule_keyword(args):
    if args[0] in ['sunrise', 'sunset']:
        return {"ERROR": "Cannot delete sunrise or sunset"}
    elif args[0] in app.config.schedule_keywords.keys():
        keyword = args[0]
    else:
        return {"ERROR": "Keyword does not exist"}

    # Remove all existing rules using keyword
    for i in app.config.schedule:
        if keyword in app.config.schedule[i].keys():
            del app.config.schedule[i][keyword]

    del app.config.schedule_keywords[keyword]
    # Schedule queue rebuild after connection closes (blocks for several seconds)
    SoftwareTimer.timer.create(1200, app.config.build_queue, "rebuild_queue")
    return {"Keyword removed": args[0]}


@app.route("save_schedule_keywords")
def save_schedule_keywords(args):
    config = read_config_from_disk()
    config['metadata']['schedule_keywords'] = app.config.schedule_keywords
    write_config_to_disk(config)
    return {"Success": "Keywords written to disk"}


@app.route("get_attributes")
@app.required_args(1)
@app.get_target_instance
def get_attributes(target, args):
    return target.get_attributes()


@app.route("condition_met")
@app.required_args(1)
@app.get_target_instance
def condition_met(target, args):
    if not is_sensor(target.name):
        return {"ERROR": "Must specify sensor"}
    else:
        return {"Condition": target.condition_met()}


@app.route("trigger_sensor")
@app.required_args(1)
@app.get_target_instance
def trigger_sensor(target, args):
    if not is_sensor(target.name):
        return {"ERROR": "Must specify sensor"}

    if target.trigger():
        return {"Triggered": target.name}
    else:
        return {"ERROR": f"Cannot trigger {target._type} sensor type"}


@app.route("turn_on")
@app.required_args(1)
@app.get_target_instance
def turn_on(target, args):
    if not is_device(target.name):
        return {"ERROR": "Can only turn on/off devices, use enable/disable for sensors"}

    if not target.enabled:
        return {"ERROR": f"{target.name} is disabled, please enable before turning on"}

    if target.send(1):
        target.state = True
        return {"On": target.name}
    else:
        return {"ERROR": f"Unable to turn on {target.name}"}


@app.route("turn_off")
@app.required_args(1)
@app.get_target_instance
def turn_off(target, args):
    if not is_device(target.name):
        return {"ERROR": "Can only turn on/off devices, use enable/disable for sensors"}

    if target.send(0):
        target.state = False
        return {"Off": target.name}
    else:
        return {"ERROR": f"Unable to turn off {target.name}"}


@app.route("get_temp")
def get_temp(args):
    for sensor in app.config.sensors:
        if sensor._type == "si7021":
            return {"Temp": sensor.fahrenheit()}
    else:
        return {"ERROR": "No temperature sensor configured"}


@app.route("get_humid")
def get_humid(args):
    for sensor in app.config.sensors:
        if sensor._type == "si7021":
            return {"Humidity": sensor.temp_sensor.relative_humidity}
    else:
        return {"ERROR": "No temperature sensor configured"}


@app.route("get_climate_data")
def get_climate_data(args):
    for sensor in app.config.sensors:
        if sensor._type == "si7021":
            data = {}
            data["temp"] = sensor.fahrenheit()
            data["humid"] = sensor.temp_sensor.relative_humidity
            return data
    else:
        return {"ERROR": "No temperature sensor configured"}


@app.route("clear_log")
def clear_log(args):
    try:
        # Close file, remove
        logging.root.handlers[0].close()
        os.remove('app.log')

        # Create new handler, set format
        h = logging.FileHandler('app.log')
        h.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(message)s'))

        # Replace old handler with new
        logging.root.handlers.clear()
        logging.root.addHandler(h)

        log.info("Deleted old log (API request)")

        return {"clear_log": "success"}
    except OSError:
        return {"ERROR": "no log file found"}


@app.route("ir_key")
@app.required_args(2)
def ir_key(args):
    try:
        blaster = app.config.ir_blaster
    except AttributeError:
        return {"ERROR": "No IR blaster configured"}

    target = args[0]
    key = args[1]

    if target not in blaster.codes:
        return {"ERROR": f'No codes found for target "{target}"'}

    if not key.lower() in blaster.codes[target]:
        return {"ERROR": f'Target "{target}" has no key "{key}"'}

    else:
        blaster.send(target, key.lower())
        return {target: key}


@app.route("backlight")
@app.required_args(1)
def backlight(args):
    try:
        blaster = app.config.ir_blaster
    except AttributeError:
        return {"Error": "No IR blaster configured"}

    if not args[0] == "on" and not args[0] == "off":
        return {'ERROR': 'Backlight setting must be "on" or "off"'}
    else:
        blaster.backlight(args[0])
        return {"backlight": args[0]}
