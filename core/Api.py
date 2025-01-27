# pylint: disable=protected-access

import os
import io
import re
import gc
import json
import asyncio
import logging
from math import isnan
from asyncio import Lock
from micropython import mem_info
import app_context
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
TIMESTAMP_REGEX = r'^([0-1][0-9]|2[0-3]):[0-5][0-9]$'

# Error constants
INVALID_SYNTAX_ERROR = {"ERROR": "Invalid syntax"}
TARGET_MISSING_ERROR = {"ERROR": "Instance not found, use status to see options"}


async def reboot_task():
    '''Ensure API call complete, connection closed before rebooting.
    Avoids rebooting before client receives response (reboot endpoint).
    '''
    async with lock:
        reboot()


async def run_macro_task(macro_name):
    '''Ensure API call complete, connection closed before running macro.
    Avoids connection timeout during long-running (>5 second) macros.
    '''
    async with lock:
        await app_context.config_instance.ir_blaster.run_macro_coro(macro_name)


class MemInfoParser(io.IOBase):
    '''Custom stream-like object used to parse micropython.mem_info output for
    mem_info endpoint. Parses free memory, max new split, and max free size and
    exposes results as class attributes.
    '''

    def __init__(self):
        self.free = None
        self.max_new_split = None
        self.max_free_sz = None
        # Receives bytes passed to write method, need to buffer because write
        # doesn't always receive a complete line ending with \n
        self._buffer = b''

    def write(self, data):
        '''Receives byte chunks written to stream.'''

        self._buffer += data
        # Process lines ending with \n until none left in _buffer
        while True:
            newline_index = self._buffer.find(b'\n')
            if newline_index == -1:
                # No newlines left
                break
            # Pass full line to _process_line, remove from _buffer
            self._process_line(self._buffer[:newline_index])
            self._buffer = self._buffer[newline_index + 1:]
        gc.collect()

    def _process_line(self, line):
        '''Takes full line (ending with newline char), detects target params
        (free, max new split, max free sz), parses value, saves in attributes.
        '''

        # Convert bytes to string to use find method
        if b'GC:' in line:
            self.free = self._extract_value(line, b'free: ')
            self.max_new_split = self._extract_value(line, b'max new split: ')
        elif b'max free sz: ' in line:
            self.max_free_sz = self._extract_value(line, b'max free sz: ')

    def _extract_value(self, line, key):
        '''Takes line and name of parameter to extract, returns value.
        Name must include colon and trailing space (find correct index).
        '''

        idx = line.find(key)
        if idx != -1:
            # Find index of first digit of value
            start = idx + len(key)
            end = start
            # Iterate until first non-digit char (ascii codes, iterating bytes)
            while end < len(line) and 48 <= line[end] <= 57:
                end += 1
            try:
                return int(line[start:end])
            except ValueError:  # pragma: no cover
                return None
        return None  # pragma: no cover


class Api:
    '''API backend, listens for requests and calls correct handler function.

    Starts listening on port 8123 when run coroutine is added to event loop.

    This class contains a handler function for each supported endpoint. Each
    handler has the same name as the endpoint, accepts a single arg (list of
    args received with the request), and returns a dict which is serialized
    and returned to the client. If the request is invalid or an error occurs
    the function should return a dict with a single "ERROR" key.

    All class methods which are NOT endpoint handler functions must start with
    an underscore (this prevents them from being called with an API request).
    '''

    def __init__(self, host='0.0.0.0', port=8123, backlog=5, timeout=20):
        self.host = host
        self.port = port
        self.backlog = backlog
        self.timeout = timeout

    async def _run(self):
        '''Starts asyncio server listening for API requests.'''
        await asyncio.start_server(
            self._run_client,
            host=self.host,
            port=self.port,
            backlog=self.backlog
        )
        print_with_timestamp('API: Awaiting client connection.\n')
        log.info("API ready")

    async def _run_client(self, sreader, swriter):
        '''Handler for JSON and HTTP API requests.

        JSON request: Expects serialized list with endpoint as first item, args
                      passed to handler function as remaining items.
        HTTP request: Expects GET request to /endpoint with args passed to
                      handler in querystring.

        Looks up endpoint method using getattr(self), passes args to to method
        if found, returns error if endpoint does not exist.
        '''
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
                path, args = await self._parse_http_request(req)
                log.debug('received HTTP request, endpoint: %s, args: %s', path, args)

                # Read until end of headers
                while True:
                    line = await asyncio.wait_for(sreader.readline(), self.timeout)
                    # Sequence indicates end of headers
                    if line == b"\r\n":
                        break

            # Raw JSON request (faster than HTTP, used by CLI, frontend, ApiTarget devices)
            else:
                http = False

                try:
                    # Convert serialized json to list, get path and args
                    data = json.loads(req)
                    path = data[0]
                    args = data[1:]
                    log.debug('received async request, endpoint: %s, args: %s', path, args)
                except ValueError:
                    # Return error if request JSON is invalid
                    swriter.write(json.dumps({"ERROR": "Syntax error in received JSON"}).encode())
                    await swriter.drain()
                    raise OSError  # pylint: disable=W0707

            # Prevent calling non-endpoint class methods
            if path.startswith('_'):
                await self._invalid_endpoint_error(swriter, path, http)
                await swriter.drain()
                raise OSError

            # Acquire lock, prevent multiple endpoints running simultaneously
            # Ensures response sent + connection closed before reboot task runs
            async with lock:
                # Find endpoint matching path, call handler function and pass args
                try:
                    # Call handler, receive reply for client
                    reply = getattr(self, path)(args)

                # Return error if no match found
                except AttributeError:
                    await self._invalid_endpoint_error(swriter, path, http)

                # Return endpoint reply to client
                else:
                    if http:
                        # Send headers before reply
                        swriter.write(
                            "HTTP/1.0 200 NA\r\nContent-Type: application/json\r\n\r\n".encode()
                        )
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

    async def _parse_http_request(self, req):
        '''Takes HTTP request (ex: "GET /status HTTP/1.1").
        Returns requested endpoint and list of args from querystring.
        '''

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

    async def _invalid_endpoint_error(self, swriter, path, http=False):
        '''Takes open stream writer instance, invalid endpoint name, and http
        bool (adds 404 header if True). Writes invalid endpoint error message
        to stream and logs the failed request to app.log.
        '''
        if http:
            # Send headers before error
            swriter.write(
                "HTTP/1.0 404 NA\r\nContent-Type: application/json\r\n\r\n".encode()
            )
        swriter.write(json.dumps({"ERROR": "Invalid command"}).encode())
        log.error('received invalid command (%s)', path)

    def reboot(self, args):
        '''Reboots ESP32 (hard reset).'''
        asyncio.create_task(reboot_task())
        return "Rebooting"

    def status(self, args):
        '''Returns status JSON with current state of all devices and sensors.'''
        return app_context.config_instance.get_status()

    def enable(self, args):
        '''Takes device or sensor ID, calls enable method.'''
        if len(args) < 1:
            return INVALID_SYNTAX_ERROR

        target = app_context.config_instance.find(args.pop(0))
        if not target:
            return TARGET_MISSING_ERROR

        target.enable()
        app_context.timer_instance.cancel(f"{target.name}_enable_in")
        return {"Enabled": target.name}

    def enable_in(self, args):
        '''Takes device or sensor ID and delay (minutes, int), creates timer to
        call enable method after requested delay.
        '''
        if len(args) < 2:
            return INVALID_SYNTAX_ERROR

        target = app_context.config_instance.find(args.pop(0))
        if not target:
            return TARGET_MISSING_ERROR

        try:
            period = float(args[0]) * 60000
            if isnan(period):
                raise ValueError
        except (ValueError, TypeError):
            return {"ERROR": "Delay argument must be int or float"}
        app_context.timer_instance.create(
            period,
            target.enable,
            f"{target.name}_enable_in"
        )
        return {"Enabled": target.name, "Enable_in_seconds": period / 1000}

    def disable(self, args):
        '''Takes device or sensor ID, calls disable method.'''
        if len(args) < 1:
            return INVALID_SYNTAX_ERROR

        target = app_context.config_instance.find(args.pop(0))
        if not target:
            return TARGET_MISSING_ERROR

        target.disable()
        app_context.timer_instance.cancel(f"{target.name}_enable_in")
        return {"Disabled": target.name}

    def disable_in(self, args):
        '''Takes device or sensor ID and delay (minutes, int), creates timer to
        call enable method after requested delay.
        '''
        if len(args) < 2:
            return INVALID_SYNTAX_ERROR

        target = app_context.config_instance.find(args.pop(0))
        if not target:
            return TARGET_MISSING_ERROR

        try:
            period = float(args[0]) * 60000
            if isnan(period):
                raise ValueError
        except (ValueError, TypeError):
            return {"ERROR": "Delay argument must be int or float"}
        app_context.timer_instance.create(
            period,
            target.disable,
            f"{target.name}_enable_in"
        )
        return {"Disabled": target.name, "Disable_in_seconds": period / 1000}

    def set_rule(self, args):
        '''Takes device or sensor ID and new rule, passes rule to set_rule method.
        Returns error if rule is not valid.
        '''
        if len(args) < 2:
            return INVALID_SYNTAX_ERROR

        target = app_context.config_instance.find(args.pop(0))
        if not target:
            return TARGET_MISSING_ERROR

        rule = args[0]

        # Replace url-encoded forward slashes (fade rules)
        if "%2F" in str(rule):
            rule = rule.replace("%2F", "/")

        if target.set_rule(rule):
            return {target.name: rule}
        return {"ERROR": "Invalid rule"}

    def increment_rule(self, args):
        '''Takes device or sensor ID and amount (int) to increment current_rule.
        Target instance must have int or float current_rule. Returns error if
        unable to increment current_rule.
        '''
        if len(args) < 2:
            return INVALID_SYNTAX_ERROR

        target = app_context.config_instance.find(args.pop(0))
        if not target:
            return TARGET_MISSING_ERROR

        if "increment_rule" not in dir(target):
            return {"ERROR": "Unsupported target, must accept int or float rule"}

        response = target.increment_rule(args[0])
        if response is True:
            return {target.name: target.current_rule}
        if response is False:
            return {"ERROR": "Invalid rule"}
        return response

    def reset_rule(self, args):
        '''Takes device or sensor ID, resets current_rule to scheduled_rule.'''
        if len(args) < 1:
            return INVALID_SYNTAX_ERROR

        target = app_context.config_instance.find(args.pop(0))
        if not target:
            return TARGET_MISSING_ERROR

        if target.current_rule != target.scheduled_rule:
            target.set_rule(target.scheduled_rule)
            return {
                target.name: "Reverted to scheduled rule",
                "current_rule": target.current_rule
            }
        return {
            target.name: "Rule already matches scheduled rule",
            "current_rule": target.current_rule
        }

    def reset_all_rules(self, args):
        '''Resets current_rule of all devices and sensors to scheduled_rule.'''
        response = {}
        response["New rules"] = {}

        for device in app_context.config_instance.devices:
            if device.current_rule != device.scheduled_rule:
                device.set_rule(device.scheduled_rule)
                response["New rules"][device.name] = device.current_rule

        for sensor in app_context.config_instance.sensors:
            if sensor.current_rule != sensor.scheduled_rule:
                sensor.set_rule(sensor.scheduled_rule)
                response["New rules"][sensor.name] = sensor.current_rule

        return response

    def get_schedule_rules(self, args):
        '''Takes device or sensor ID, returns dict of schedule rules.'''
        if len(args) < 1:
            return INVALID_SYNTAX_ERROR

        target = app_context.config_instance.find(args.pop(0))
        if not target:
            return TARGET_MISSING_ERROR

        return target.schedule

    def add_schedule_rule(self, args):
        '''Takes device or sensor ID, HH:MM timestamp or schedule keyword, and rule
        to apply at requested timestamp. Creates schedule rule in memory (does not
        persist after reboot).
        '''
        if len(args) < 3:
            return INVALID_SYNTAX_ERROR

        target = app_context.config_instance.find(args.pop(0))
        if not target:
            return TARGET_MISSING_ERROR

        if re.match(TIMESTAMP_REGEX, args[0]):
            timestamp = args[0]
        elif args[0] in app_context.config_instance.schedule_keywords:
            timestamp = args[0]
        else:
            return {"ERROR": "Timestamp format must be HH:MM (no AM/PM) or schedule keyword"}

        valid = target.rule_validator(args[1])

        if valid is False:
            return {"ERROR": "Invalid rule"}

        if timestamp in target.schedule and (not len(args) >= 3 or not args[2] == "overwrite"):
            return {"ERROR": f"Rule already exists at {timestamp}, add 'overwrite' arg to replace"}

        target.schedule[timestamp] = valid
        # Schedule queue rebuild after connection closes (blocks for several seconds)
        app_context.timer_instance.create(
            1200,
            app_context.config_instance._build_queue,
            "rebuild_queue"
        )
        return {"Rule added": valid, "time": timestamp}

    def remove_rule(self, args):
        '''Takes device or sensor ID, HH:MM timestamp or schedule keyword of
        existing schedule rule. Removes rule from in-memory schedule (does not
        remove from config file on disk, does not persist after reboot).
        '''
        if len(args) < 2:
            return INVALID_SYNTAX_ERROR

        target = app_context.config_instance.find(args.pop(0))
        if not target:
            return TARGET_MISSING_ERROR

        if re.match(TIMESTAMP_REGEX, args[0]):
            timestamp = args[0]
        elif args[0] in app_context.config_instance.schedule_keywords:
            timestamp = args[0]
        else:
            return {"ERROR": "Timestamp format must be HH:MM (no AM/PM) or schedule keyword"}

        try:
            del target.schedule[timestamp]
            # Schedule queue rebuild after connection closes (blocks for several seconds)
            app_context.timer_instance.create(
                1200,
                app_context.config_instance._build_queue,
                "rebuild_queue"
            )
        except KeyError:
            return {"ERROR": "No rule exists at that time"}

        return {"Deleted": timestamp}

    def save_rules(self, args):
        '''Writes current in-memory schedule rules of all devices and sensors to
        config file on disk. Used to make new schedule rules persist after reboot.
        '''
        config = read_config_from_disk()

        for i in config:
            if is_device_or_sensor(i):
                config[i]["schedule"] = app_context.config_instance.find(i).schedule

        write_config_to_disk(config)
        return {"Success": "Rules written to disk"}

    def get_schedule_keywords(self, args):
        '''Teturns dict of existing schedule keywords and matching timestamps.'''
        return app_context.config_instance.schedule_keywords

    def add_schedule_keyword(self, args):
        '''Takes new schedule keyword name and matching timestamp (HH:MM). Adds to
        in-memory schedule keyword dict (does not persist after reboot).
        '''
        if len(args) < 1:
            return INVALID_SYNTAX_ERROR

        if not isinstance(args[0], dict):
            return {"ERROR": "Requires dict with keyword and timestamp"}

        keyword, timestamp = args[0].popitem()

        if re.match(TIMESTAMP_REGEX, timestamp):
            app_context.config_instance.schedule_keywords[keyword] = timestamp
            # Schedule queue rebuild after connection closes (blocks for several seconds)
            app_context.timer_instance.create(
                1200,
                app_context.config_instance._build_queue,
                "rebuild_queue"
            )
            return {"Keyword added": keyword, "time": timestamp}
        return {"ERROR": "Timestamp format must be HH:MM (no AM/PM)"}

    def remove_schedule_keyword(self, args):
        '''Takes existing schedule keyword name, removes from in-memory schedule
        keyword dict (does not persist after reboot).
        '''
        if len(args) < 1:
            return INVALID_SYNTAX_ERROR

        if args[0] in ['sunrise', 'sunset']:
            return {"ERROR": "Cannot delete sunrise or sunset"}
        if args[0] in app_context.config_instance.schedule_keywords:
            keyword = args[0]
        else:
            return {"ERROR": "Keyword does not exist"}

        # Remove all existing rules using keyword
        for device in app_context.config_instance.devices:
            if keyword in device.schedule:  # pragma: no branch
                del device.schedule[keyword]
        for sensor in app_context.config_instance.sensors:
            if keyword in sensor.schedule:
                del sensor.schedule[keyword]

        del app_context.config_instance.schedule_keywords[keyword]
        # Schedule queue rebuild after connection closes (blocks for several seconds)
        app_context.timer_instance.create(
            1200,
            app_context.config_instance._build_queue,
            "rebuild_queue"
        )
        return {"Keyword removed": args[0]}

    def save_schedule_keywords(self, args):
        '''Writes in-memory schedule keyword dict to config file on disk.
        Used to make new schedule keywords persist after reboot.
        '''
        config = read_config_from_disk()
        config['schedule_keywords'] = app_context.config_instance.schedule_keywords
        write_config_to_disk(config)
        return {"Success": "Keywords written to disk"}

    def get_attributes(self, args):
        '''Takes device or sensor ID, returns dict with all instance attributes.'''
        if len(args) < 1:
            return INVALID_SYNTAX_ERROR

        target = app_context.config_instance.find(args.pop(0))
        if not target:
            return TARGET_MISSING_ERROR

        return target.get_attributes()

    def condition_met(self, args):
        '''Takes sensor ID, returns dict with current sensor condition.'''
        if len(args) < 1:
            return INVALID_SYNTAX_ERROR

        target = app_context.config_instance.find(args.pop(0))
        if not target:
            return TARGET_MISSING_ERROR

        if not is_sensor(target.name):
            return {"ERROR": "Must specify sensor"}
        return {"Condition": target.condition_met()}

    def trigger_sensor(self, args):
        '''Takes sensor ID, calls trigger method to simulate sensor condition
        being met (turns on target devices). Returns error if sensor not supported.
        '''
        if len(args) < 1:
            return INVALID_SYNTAX_ERROR

        target = app_context.config_instance.find(args.pop(0))
        if not target:
            return TARGET_MISSING_ERROR

        if not is_sensor(target.name):
            return {"ERROR": "Must specify sensor"}

        if target.trigger():
            return {"Triggered": target.name}
        return {"ERROR": f"Cannot trigger {target._type} sensor type"}

    def turn_on(self, args):
        '''Takes device ID, turns device on. Returns error if failed to turn on.'''
        if len(args) < 1:
            return INVALID_SYNTAX_ERROR

        target = app_context.config_instance.find(args.pop(0))
        if not target:
            return TARGET_MISSING_ERROR

        if not is_device(target.name):
            return {"ERROR": "Can only turn on/off devices, use enable/disable for sensors"}

        if not target.enabled:
            return {"ERROR": f"{target.name} is disabled, please enable before turning on"}

        if target.send(1):
            target.state = True
            return {"On": target.name}
        return {"ERROR": f"Unable to turn on {target.name}"}

    def turn_off(self, args):
        '''Takes device ID, turns device off. Returns error if failed to turn off.'''
        if len(args) < 1:
            return INVALID_SYNTAX_ERROR

        target = app_context.config_instance.find(args.pop(0))
        if not target:
            return TARGET_MISSING_ERROR

        if not is_device(target.name):
            return {"ERROR": "Can only turn on/off devices, use enable/disable for sensors"}

        if target.send(0):
            target.state = False
            return {"Off": target.name}
        return {"ERROR": f"Unable to turn off {target.name}"}

    def get_temp(self, args):
        '''Returns current temperature reading in configured units.
        Returns error if no temperature sensor configured.
        '''
        for sensor in app_context.config_instance.sensors:
            if sensor._type in ["si7021", "dht22"]:
                return {"Temp": sensor.get_temperature()}
        return {"ERROR": "No temperature sensor configured"}

    def get_humid(self, args):
        '''Returns current relative humidity reading.
        Returns error if no temperature/humidity sensor configured.
        '''
        for sensor in app_context.config_instance.sensors:
            if sensor._type in ["si7021", "dht22"]:
                return {"Humidity": sensor.get_humidity()}
        return {"ERROR": "No temperature sensor configured"}

    def get_climate_data(self, args):
        '''Returns current temperature and relative humidity readings.
        Returns error if no temperature/humidity sensor configured.
        '''
        for sensor in app_context.config_instance.sensors:
            if sensor._type in ["si7021", "dht22"]:
                return {
                    "temp": sensor.get_temperature(),
                    "humid": sensor.get_humidity()
                }
        return {"ERROR": "No temperature sensor configured"}

    def clear_log(self, args):
        '''Clears app.log contents.'''
        try:
            clear_log()
            log.critical("Deleted old log (API request)")
            return {"clear_log": "success"}
        except OSError:
            return {"ERROR": "no log file found"}

    def set_log_level(self, args):
        '''Takes log level (CRITICAL, ERROR, WARNING, INFO, or DEBUG).
        Writes new log level to disk (takes effect on next reboot).
        '''
        if len(args) < 1:
            return INVALID_SYNTAX_ERROR

        if args[0] not in logging._nameToLevel:
            return {
                "ERROR": "Unsupported log level",
                "options": list(logging._nameToLevel.keys())
            }
        with open("log_level.py", "w", encoding="utf-8") as file:
            file.write(f"LOG_LEVEL = '{args[0]}'")
        log.critical("Log level changed to %s", args[0])
        return {"Success": "Log level set (takes effect after reboot)"}

    def ir_key(self, args):
        '''Takes IR target device and key name, sends code with IR Blaster.
        Returns error if target/key invalid or no IR Blaster configured.
        '''
        if len(args) < 2:
            return INVALID_SYNTAX_ERROR

        if not app_context.config_instance.ir_blaster:
            return {"ERROR": "No IR blaster configured"}

        target = args[0]
        key = args[1]

        if target not in app_context.config_instance.ir_blaster.codes:
            return {"ERROR": f'No codes found for target "{target}"'}

        if not key.lower() in app_context.config_instance.ir_blaster.codes[target]:
            return {"ERROR": f'Target "{target}" has no key "{key}"'}

        app_context.config_instance.ir_blaster.send(target, key.lower())
        return {target: key}

    def ir_get_existing_macros(self, args):
        '''Returns dict with existing IR Blaster macros.
        Returns error if no IR Blaster configured.
        '''
        if not app_context.config_instance.ir_blaster:
            return {"ERROR": "No IR blaster configured"}
        return app_context.config_instance.ir_blaster.get_existing_macros()

    def ir_create_macro(self, args):
        '''Takes name of new IR Blaster macro, adds to in-memory macros dict (does
        not persist after reboot). Returns error if no IR Blaster configured.
        '''
        if len(args) < 1:
            return INVALID_SYNTAX_ERROR

        if not app_context.config_instance.ir_blaster:
            return {"ERROR": "No IR blaster configured"}
        try:
            app_context.config_instance.ir_blaster.create_macro(args[0])
            return {"Macro created": args[0]}
        except ValueError as error:
            return {"ERROR": str(error)}

    def ir_delete_macro(self, args):
        '''Takes name of existing IR Blaster macro, removes from in-memory macros
        dict (does not persist after reboot). Returns error if no IR Blaster
        configured.
        '''
        if len(args) < 1:
            return INVALID_SYNTAX_ERROR

        if not app_context.config_instance.ir_blaster:
            return {"ERROR": "No IR blaster configured"}
        try:
            app_context.config_instance.ir_blaster.delete_macro(args[0])
            return {"Macro deleted": args[0]}
        except ValueError as error:
            return {"ERROR": str(error)}

    def ir_save_macros(self, args):
        '''Writes in-memory IR Blaster macros dict to config file on disk.
        Used to make new schedule rules persist after reboot.
        '''
        if not app_context.config_instance.ir_blaster:
            return {"ERROR": "No IR blaster configured"}
        app_context.config_instance.ir_blaster.save_macros()
        return {"Success": "Macros written to disk"}

    def ir_add_macro_action(self, args):
        '''Takes 3 required args (existing IR Blaster macro name, IR target name,
        IR key name) and 2 optional args (ms delay after key, key repeat int).
        Adds action to in-memory IR macros dict (does not persist after reboot).
        '''
        if len(args) < 3:
            return INVALID_SYNTAX_ERROR

        if not app_context.config_instance.ir_blaster:
            return {"ERROR": "No IR blaster configured"}
        try:
            app_context.config_instance.ir_blaster.add_macro_action(*args)
            return {"Macro action added": args}
        except ValueError as error:
            return {"ERROR": str(error)}

    def ir_run_macro(self, args):
        '''Takes name of existing IR Blaster macro, runs all actions.
        Returns error if no IR Blaster configured.
        '''
        if len(args) < 1:
            return INVALID_SYNTAX_ERROR

        if not app_context.config_instance.ir_blaster:
            return {"ERROR": "No IR blaster configured"}
        if args[0] not in app_context.config_instance.ir_blaster.macros.keys():
            return {"ERROR": f"Macro {args[0]} does not exist, use create_macro to add"}

        # Create task, return response immediately
        asyncio.create_task(run_macro_task(args[0]))
        return {"Ran macro": args[0]}

    def set_gps_coords(self, args):
        '''Takes dict with latitude and longitude keys containing coordinates used
        to get sunrise and sunset times, writes to config file on disk.
        '''
        if len(args) < 1:
            return INVALID_SYNTAX_ERROR

        if (
            not isinstance(args[0], dict)
            or 'latitude' not in args[0]
            or 'longitude' not in args[0]
        ):
            return {"ERROR": "Requires dict with longitude and latitude keys"}

        if not is_latitude(args[0]['latitude']):
            return {"ERROR": "Latitude must be between -90 and 90"}
        if not is_longitude(args[0]['longitude']):
            return {"ERROR": "Longitude must be between -180 and 180"}

        config = read_config_from_disk()
        config['metadata']['gps'] = {
            'lat': args[0]['latitude'],
            'lon': args[0]['longitude']
        }
        write_config_to_disk(config)
        return {"Success": "GPS coordinates set"}

    def load_cell_tare(self, args):
        '''Takes sensor ID of load cell sensor, calls tare_sensor method.'''
        if len(args) < 1:
            return INVALID_SYNTAX_ERROR

        target = app_context.config_instance.find(args.pop(0))
        if not target:
            return TARGET_MISSING_ERROR

        if target._type != 'load-cell':
            return {"ERROR": "Must specify load cell sensor"}
        target.tare_sensor()
        return {"Success": "Sensor tared"}

    def load_cell_read(self, args):
        '''Takes sensor ID of load cell sensor, returns raw sensor reading.'''
        if len(args) < 1:
            return INVALID_SYNTAX_ERROR

        target = app_context.config_instance.find(args.pop(0))
        if not target:
            return TARGET_MISSING_ERROR

        if target._type != 'load-cell':
            return {"ERROR": "Must specify load cell sensor"}
        return {"Raw": target.get_raw_reading()}

    def mem_info(self, args):
        '''Returns dict with parameters from micropython.mem_info output.'''

        # Duplicate terminal output to custom stream parser
        parser = MemInfoParser()
        os.dupterm(parser)
        # Print mem_info to terminal (parser extracts params)
        mem_info()
        # Reset terminal output, return parsed parameters
        os.dupterm(None)
        return {
            'free': parser.free,
            'max_new_split': parser.max_new_split,
            'max_free_sz': parser.max_free_sz
        }
