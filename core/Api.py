import re
import gc
import json
import asyncio
import logging
from math import isnan
from asyncio import Lock
from functools import wraps
import SoftwareTimer
from util import (
    is_device,
    is_sensor,
    is_device_or_sensor,
    is_latitude,
    is_longitude,
    reboot,
    clear_log,
    read_config_from_disk,
    write_config_to_disk,
    print_with_timestamp
)

# Set name for module's log lines
log = logging.getLogger("API")

lock = Lock()

# Matches HH:MM
timestamp_regex = r'^([0-1][0-9]|2[0-3]):[0-5][0-9]$'


# Ensure API call complete, connection closed before rebooting (reboot endpoint)
async def reboot_task():
    async with lock:
        reboot()


# Ensure API call complete, connection closed before running macro
# Avoids connection timeout during long-running (>5 second) macros
async def run_macro_task(blaster, macro_name):
    async with lock:
        await blaster.run_macro_coro(macro_name)


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
        self.server = await asyncio.start_server(self.run_client, host=self.host, port=self.port, backlog=self.backlog)
        print_with_timestamp('API: Awaiting client connection.\n')
        log.info("API ready")

    async def run_client(self, sreader, swriter):
        try:
            # Read client request
            req = await asyncio.wait_for(sreader.readline(), self.timeout)
            req = req.decode()

            # Received null (client closed write stream), skip to end and close read stream
            if not req:
                raise OSError

            # HTTP request (slow but can be made from browser)
            if str(req).startswith("GET"):
                http = True
                path, args = await self.parse_http_request(req)
                log.debug('received HTTP request, endpoint: %s, args: %s', path, args)

                # Read until end of headers
                while True:
                    line = await asyncio.wait_for(sreader.readline(), self.timeout)
                    # Sequence indicates end of headers
                    if line == b"\r\n":
                        break

            # Raw JSON request (faster than HTTP, used by api_client, frontend, ApiTarget device type)
            else:
                http = False

                try:
                    # Convert serialized json to dict, get path and args
                    data = json.loads(req)
                    path = data[0]
                    args = data[1:]
                    log.debug('received async request, endpoint: %s, args: %s', path, args)
                except ValueError:
                    # Return error if request JSON is invalid
                    swriter.write(json.dumps({"ERROR": "Syntax error in received JSON"}).encode())
                    await swriter.drain()
                    raise OSError

            # Acquire lock, prevent multiple endpoints running simultaneously
            # Ensures response sent + connection closed before reboot task runs
            async with lock:
                # Find endpoint matching path, call handler function and pass args
                try:
                    # Call handler, receive reply for client
                    reply = self.url_map[path](args)

                # Return error if no match found
                except KeyError:
                    if http:
                        # Send headers before error
                        swriter.write("HTTP/1.0 404 NA\r\nContent-Type: application/json\r\n\r\n".encode())
                    swriter.write(json.dumps({"ERROR": "Invalid command"}).encode())
                    log.error('received invalid command (%s)', path)

                # Return endpoint reply to client
                else:
                    if http:
                        # Send headers before reply
                        swriter.write("HTTP/1.0 200 NA\r\nContent-Type: application/json\r\n\r\n".encode())
                    swriter.write(json.dumps(reply).encode())

                # Send response, close stream
                await swriter.drain()
                swriter.close()
                await swriter.wait_closed()

        except (OSError, asyncio.TimeoutError):
            # Close stream
            swriter.close()
            await swriter.wait_closed()

        # Reduce memory fragmentation from repeated requests
        gc.collect()

    # Takes HTTP request (ex: "GET /status HTTP/1.1")
    # Returns requested endpoint and list of args
    async def parse_http_request(self, req):
        # Drop everything except path and querystring
        req = req.split()[1]

        # Split path and querystring (if present)
        # Remove leading / from path, convert querystring to list of args
        if "?" in req:
            path, querystring = req.split("?")
            path = path[1:]
            args = querystring.split("/")
        else:
            path = req[1:]
            args = ""

        return path, args


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
    SoftwareTimer.timer.cancel(f"{target.name}_enable_in")
    return {"Enabled": target.name}


@app.route("enable_in")
@app.required_args(2)
@app.get_target_instance
def enable_in(target, args):
    try:
        period = float(args[0]) * 60000
        if isnan(period):
            raise ValueError
    except (ValueError, TypeError):
        return {"ERROR": "Delay argument must be int or float"}
    SoftwareTimer.timer.create(period, target.enable, f"{target.name}_enable_in")
    return {"Enabled": target.name, "Enable_in_seconds": period / 1000}


@app.route("disable")
@app.required_args(1)
@app.get_target_instance
def disable(target, args):
    target.disable()
    SoftwareTimer.timer.cancel(f"{target.name}_enable_in")
    return {"Disabled": target.name}


@app.route("disable_in")
@app.required_args(2)
@app.get_target_instance
def disable_in(target, args):
    try:
        period = float(args[0]) * 60000
        if isnan(period):
            raise ValueError
    except (ValueError, TypeError):
        return {"ERROR": "Delay argument must be int or float"}
    SoftwareTimer.timer.create(period, target.disable, f"{target.name}_enable_in")
    return {"Disabled": target.name, "Disable_in_seconds": period / 1000}


@app.route("set_rule")
@app.required_args(2)
@app.get_target_instance
def set_rule(target, args):
    rule = args[0]

    # Replace url-encoded forward slashes (fade rules)
    if "%2F" in str(rule):
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

    response = target.increment_rule(args[0])
    if response is True:
        return {target.name: target.current_rule}
    elif response is False:
        return {"ERROR": "Invalid rule"}
    else:
        return response


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

    if valid is False:
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
        if sensor._type in ["si7021", "dht22"]:
            return {"Temp": sensor.get_temperature()}
    else:
        return {"ERROR": "No temperature sensor configured"}


@app.route("get_humid")
def get_humid(args):
    for sensor in app.config.sensors:
        if sensor._type in ["si7021", "dht22"]:
            return {"Humidity": sensor.get_humidity()}
    else:
        return {"ERROR": "No temperature sensor configured"}


@app.route("get_climate_data")
def get_climate_data(args):
    for sensor in app.config.sensors:
        if sensor._type in ["si7021", "dht22"]:
            return {
                "temp": sensor.get_temperature(),
                "humid": sensor.get_humidity()
            }
    else:
        return {"ERROR": "No temperature sensor configured"}


@app.route("clear_log")
def clear_log_file(args):
    try:
        clear_log()
        log.critical("Deleted old log (API request)")
        return {"clear_log": "success"}
    except OSError:
        return {"ERROR": "no log file found"}


@app.route("set_log_level")
@app.required_args(1)
def set_log_level(args):
    if args[0] not in logging._nameToLevel:
        return {
            "ERROR": "Unsupported log level",
            "options": list(logging._nameToLevel.keys())
        }
    with open("log_level.py", "w") as file:
        file.write(f"LOG_LEVEL = '{args[0]}'")
    log.critical("Log level changed to %s", args[0])
    return {"Success": "Log level set (takes effect after reboot)"}


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


@app.route("ir_get_existing_macros")
def ir_get_existing_macros(args):
    try:
        blaster = app.config.ir_blaster
    except AttributeError:
        return {"ERROR": "No IR blaster configured"}
    return blaster.get_existing_macros()


@app.route("ir_create_macro")
@app.required_args(1)
def ir_create_macro(args):
    try:
        blaster = app.config.ir_blaster
    except AttributeError:
        return {"ERROR": "No IR blaster configured"}

    try:
        blaster.create_macro(args[0])
        return {"Macro created": args[0]}
    except ValueError as error:
        return {"ERROR": str(error)}


@app.route("ir_delete_macro")
@app.required_args(1)
def ir_delete_macro(args):
    try:
        blaster = app.config.ir_blaster
    except AttributeError:
        return {"ERROR": "No IR blaster configured"}

    try:
        blaster.delete_macro(args[0])
        return {"Macro deleted": args[0]}
    except ValueError as error:
        return {"ERROR": str(error)}


@app.route("ir_save_macros")
def ir_save_macros(args):
    try:
        blaster = app.config.ir_blaster
    except AttributeError:
        return {"ERROR": "No IR blaster configured"}
    blaster.save_macros()
    return {"Success": "Macros written to disk"}


@app.route("ir_add_macro_action")
@app.required_args(3)
def ir_add_macro_action(args):
    try:
        blaster = app.config.ir_blaster
    except AttributeError:
        return {"ERROR": "No IR blaster configured"}

    try:
        blaster.add_macro_action(*args)
        return {"Macro action added": args}
    except ValueError as error:
        return {"ERROR": str(error)}


@app.route("ir_run_macro")
@app.required_args(1)
def ir_run_macro(args):
    try:
        blaster = app.config.ir_blaster
    except AttributeError:
        return {"ERROR": "No IR blaster configured"}
    if args[0] not in blaster.macros.keys():
        return {"ERROR": f"Macro {args[0]} does not exist, use create_macro to add"}

    # Create task, return response immediately
    asyncio.create_task(run_macro_task(blaster, args[0]))
    return {"Ran macro": args[0]}


@app.route("set_gps_coords")
@app.required_args(1)
def set_gps_coords(args):
    if not isinstance(args[0], dict) or 'latitude' not in args[0].keys() or 'longitude' not in args[0].keys():
        return {"ERROR": "Requires dict with longitude and latitude keys"}

    if not is_latitude(args[0]['latitude']):
        return {"ERROR": "Latitude must be between -90 and 90"}
    elif not is_longitude(args[0]['longitude']):
        return {"ERROR": "Longitude must be between -180 and 180"}

    config = read_config_from_disk()
    config['metadata']['gps'] = {
        'lat': args[0]['latitude'],
        'lon': args[0]['longitude']
    }
    write_config_to_disk(config)
    return {"Success": "GPS coordinates set"}


@app.route("load_cell_tare")
@app.required_args(1)
@app.get_target_instance
def load_cell_tare(target, args):
    if target._type != 'load-cell':
        return {"ERROR": "Must specify load cell sensor"}
    target.tare_sensor()
    return {"Success": "Sensor tared"}


@app.route("load_cell_read")
@app.required_args(1)
@app.get_target_instance
def load_cell_read(target, args):
    if target._type != 'load-cell':
        return {"ERROR": "Must specify load cell sensor"}
    return {"Raw": target.get_raw_reading()}
