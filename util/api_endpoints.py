'''Contains functions used by client-side tools (CLI.api_client, django webapp)
to call each endpoint supported by ESP32 firmware (see core.Api).

Each function takes 2 arguments:
- Target ESP32 IP address
- List of endpoint arguments (eg set_rule could take ['device1', 'enabled'])

All functions return the response received from ESP32. Some functions validate
arguments and return an error string without making an API call if syntax
errors are found (missing arguments, invalid arguments, etc).

All functions are added to the endpoint_map mapping dict (endpoint names as
keys, functions as values). This should be used when possible instead of
importing each function individually.
'''

import json
import asyncio
from math import isnan
from functools import wraps
from validation_constants import ir_blaster_options
from helper_functions import (
    valid_timestamp,
    is_device_or_sensor,
    is_device,
    is_sensor,
    get_schedule_keywords_dict
)

# Populated with endpoint:handler pairs by decorators below
endpoint_map = {}


def add_endpoint(url):
    '''Decorator used to populate endpoint_map'''
    def _add_endpoint(func):
        endpoint_map[url] = func
        return func
    return _add_endpoint


def requires_params(func):
    '''Decorator adds wrapper that prevents calling func with empty param list'''
    @wraps(func)
    def wrapper(ip, params):
        if len(params) == 0:
            raise SyntaxError
        return func(ip, params)
    return wrapper


def requires_device_or_sensor(error_message):
    '''Decorator factory - takes error_message returned by wrapper function if
    first param (target) is neither device nor sensor. Otherwise calls wrapped
    function with target as second arg, remaining params as 3rd arg.
    Should be placed after @requires_params
    '''
    def decorator(func):
        @wraps(func)
        def wrapper(ip, params):
            if not is_device_or_sensor(params[0]):
                return {"ERROR": error_message}
            return func(ip, params[0], params[1:])
        return wrapper
    return decorator


def requires_device(error_message):
    '''Decorator factory - takes error_message returned by wrapper function if
    first param (target) is not device. Otherwise calls wrapped function with
    target as second arg, remaining params as 3rd arg.
    Should be placed after @requires_params
    '''
    def decorator(func):
        @wraps(func)
        def wrapper(ip, params):
            if not is_device(params[0]):
                return {"ERROR": error_message}
            return func(ip, params[0], params[1:])
        return wrapper
    return decorator


def requires_sensor(error_message):
    '''Decorator factory - takes error_message returned by wrapper function if
    first param (target) is not sensor. Otherwise calls wrapped function with
    target as second arg, remaining params as 3rd arg.
    Should be placed after @requires_params
    '''
    def decorator(func):
        @wraps(func)
        def wrapper(ip, params):
            if not is_sensor(params[0]):
                return {"ERROR": error_message}
            return func(ip, params[0], params[1:])
        return wrapper
    return decorator


async def request(ip, msg):
    '''Takes node IP and list with API endpoint followed by arguments (if any).
    Sends request to node using asyncio streams.
    '''

    # Open connection (5 second timeout)
    try:
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(ip, 8123),
            timeout=5
        )
    except asyncio.TimeoutError:
        return "Error: Request timed out"
    except OSError:
        return "Error: Failed to connect"

    # Send message
    try:
        writer.write(f'{json.dumps(msg)}\n'.encode())
        await writer.drain()
        # Timeout prevents hang if node event loop crashed
        res = await asyncio.wait_for(reader.read(), timeout=5)
    except asyncio.TimeoutError:
        return "Error: Timed out waiting for response"
    except OSError:
        return "Error: Request failed"

    # Read response, close connection
    try:
        response = json.loads(res)
    except ValueError:
        return "Error: Unable to decode response"
    writer.close()
    await writer.wait_closed()

    return response


@add_endpoint("status")
def status(ip, _):
    '''Makes /status API call to requested IP, returns response.'''
    return asyncio.run(request(ip, ['status']))


@add_endpoint("reboot")
def reboot(ip, _):
    '''Makes /reboot API call to requested IP, returns response.'''
    return asyncio.run(request(ip, ['reboot']))


@add_endpoint("disable")
@requires_params
@requires_device_or_sensor("Can only disable devices and sensors")
def disable(ip, target, _):
    '''Makes /disable API call to requested IP, returns response.
    Requires device or sensor ID argument.
    '''
    return asyncio.run(request(ip, ['disable', target]))


@add_endpoint("disable_in")
@requires_params
@requires_device_or_sensor("Can only disable devices and sensors")
def disable_in(ip, target, params):
    '''Makes /disable_in API call to requested IP, returns response.
    Requires device/sensor ID and duration (int) arguments.
    '''
    try:
        period = float(params[0])
        if isnan(period):
            raise ValueError
        return asyncio.run(request(ip, ['disable_in', target, period]))
    except IndexError:
        return {"ERROR": "Please specify delay in minutes"}
    except ValueError:
        return {"ERROR": "Delay argument must be int or float"}


@add_endpoint("enable")
@requires_params
@requires_device_or_sensor("Can only enable devices and sensors")
def enable(ip, target, _):
    '''Makes /enable API call to requested IP , returns response.
    Requires device or sensor ID argument.
    '''
    return asyncio.run(request(ip, ['enable', target]))


@add_endpoint("enable_in")
@requires_params
@requires_device_or_sensor("Can only enable devices and sensors")
def enable_in(ip, target, params):
    '''Makes /enable_in API call to requested IP, returns response.
    Requires device/sensor ID and duration (int) arguments.
    '''
    try:
        period = float(params[0])
        if isnan(period):
            raise ValueError
        return asyncio.run(request(ip, ['enable_in', target, period]))
    except IndexError:
        return {"ERROR": "Please specify delay in minutes"}
    except ValueError:
        return {"ERROR": "Delay argument must be int or float"}


@add_endpoint("set_rule")
@requires_params
@requires_device_or_sensor("Can only set rules for devices and sensors")
def set_rule(ip, target, params):
    '''Makes /set_rule API call to requested IP, returns response.
    Requires device/sensor ID and new rule arguments.
    '''
    try:
        return asyncio.run(request(ip, ['set_rule', target, params[0]]))
    except IndexError:
        return {"ERROR": "Must specify new rule"}


@add_endpoint("increment_rule")
@requires_params
@requires_device_or_sensor("Target must be device or sensor with int rule")
def increment_rule(ip, target, params):
    '''Makes /increment_rule API call to requested IP, returns response.
    Requires device/sensor ID and increment amount (int) arguments.
    '''
    try:
        return asyncio.run(request(ip, ['increment_rule', target, params[0]]))
    except IndexError:
        return {"ERROR": "Must specify amount (int) to increment by"}


@add_endpoint("reset_rule")
@requires_params
@requires_device_or_sensor("Can only set rules for devices and sensors")
def reset_rule(ip, target, _):
    '''Makes /reset_rule API call to requested IP, returns response
    Requires device or sensor ID argument.
    '''
    return asyncio.run(request(ip, ['reset_rule', target]))


@add_endpoint("reset_all_rules")
def reset_all_rules(ip, _):
    '''Makes /reset_all_rules API call to requested IP, returns response.'''
    return asyncio.run(request(ip, ['reset_all_rules']))


@add_endpoint("get_schedule_rules")
@requires_params
@requires_device_or_sensor("Only devices and sensors have schedule rules")
def get_schedule_rules(ip, target, _):
    '''Makes /get_schedule_rules API call to requested IP, returns response.
    Requires device or sensor ID argument.
    '''
    return asyncio.run(request(ip, ['get_schedule_rules', target]))


@add_endpoint("add_rule")
@requires_params
@requires_device_or_sensor("Only devices and sensors have schedule rules")
def add_schedule_rule(ip, target, params):
    '''Makes /add_schedule_rule API call to requested IP, returns response.
    Requires device/sensor ID, rule timestamp/keyword, and rule value arguments.
    '''
    if len(params) > 0 and valid_timestamp(params[0]):
        timestamp = params.pop(0)
    elif len(params) > 0 and params[0] in get_schedule_keywords_dict().keys():
        timestamp = params.pop(0)
    else:
        return {"ERROR": "Must specify timestamp (HH:MM) or keyword followed by rule"}

    if len(params) == 0:
        return {"ERROR": "Must specify new rule"}

    cmd = ['add_schedule_rule', target, timestamp]

    # Add remaining args to cmd - may contain rule, or rule + overwrite
    for i in params:
        cmd.append(i)

    return asyncio.run(request(ip, cmd))


@add_endpoint("remove_rule")
@requires_params
@requires_device_or_sensor("Only devices and sensors have schedule rules")
def remove_rule(ip, target, params):
    '''Makes /remove_rule API call to requested IP, returns response.
    Requires device/sensor ID and rule timestamp/keyword arguments.
    '''
    if len(params) > 0 and valid_timestamp(params[0]):
        timestamp = params.pop(0)
    elif len(params) > 0 and params[0] in get_schedule_keywords_dict().keys():
        timestamp = params.pop(0)
    else:
        return {"ERROR": 'Must specify timestamp (HH:MM) or keyword of rule to remove'}

    return asyncio.run(request(ip, ['remove_rule', target, timestamp]))


@add_endpoint("save_rules")
def save_rules(ip, _):
    '''Makes /save_rules API call to requested IP, returns response.'''
    return asyncio.run(request(ip, ['save_rules']))


@add_endpoint("get_schedule_keywords")
def get_schedule_keywords(ip, _):
    '''Makes /get_schedule_keywords API call to requested IP, returns response.'''
    return asyncio.run(request(ip, ['get_schedule_keywords']))


@add_endpoint("add_schedule_keyword")
@requires_params
def add_schedule_keyword(ip, params):
    '''Makes /add_schedule_keyword API call to requested IP, returns response.
    Requires new keyword name and timestamp (HH:MM) arguments.
    '''
    keyword = params.pop(0)

    if len(params) > 0 and valid_timestamp(params[0]):
        timestamp = params.pop(0)
    else:
        return {"ERROR": "Timestamp format must be HH:MM (no AM/PM)"}

    cmd = ['add_schedule_keyword', {keyword: timestamp}]

    return asyncio.run(request(ip, cmd))


@add_endpoint("remove_schedule_keyword")
@requires_params
def remove_schedule_keyword(ip, params):
    '''Makes /remove_schedule_keyword API call to requested IP, returns response.
    Requires existing keyword name argument.
    '''
    cmd = ['remove_schedule_keyword', params.pop(0)]
    return asyncio.run(request(ip, cmd))


@add_endpoint("save_schedule_keywords")
def save_schedule_keywords(ip, _):
    '''Makes /save_schedule_keywords API call to requested IP, returns response.'''
    return asyncio.run(request(ip, ['save_schedule_keywords']))


@add_endpoint("get_attributes")
@requires_params
@requires_device_or_sensor("Must specify device or sensor")
def get_attributes(ip, target, _):
    '''Makes /get_attributes API call to requested IP, returns response.
    Requires device or sensor ID argument.
    '''
    return asyncio.run(request(ip, ['get_attributes', target]))


@add_endpoint("ir")
@requires_params
def ir(ip, params):
    '''Makes /ir_key API call to requested IP, returns response.
    Requires IR target name and IR key name arguments.
    '''

    # First arg must be key in ir_blaster_options dict
    target = params[0]
    if target not in ir_blaster_options:
        raise SyntaxError

    try:
        return asyncio.run(request(ip, ['ir_key', target, params[1]]))
    except IndexError:
        return {
            "ERROR": f"Must specify one of the following commands: {ir_blaster_options[target]}"
        }


@add_endpoint("ir_get_existing_macros")
def ir_get_existing_macros(ip, _):
    '''Makes /ir_get_existing_macros API call to requested IP, returns response.'''
    return asyncio.run(request(ip, ['ir_get_existing_macros']))


@add_endpoint("ir_create_macro")
@requires_params
def ir_create_macro(ip, params):
    '''Makes /ir_create_macro API call to requested IP, returns response.
    Requires new macro name argument.
    '''
    return asyncio.run(request(ip, ['ir_create_macro', params[0]]))


@add_endpoint("ir_delete_macro")
@requires_params
def ir_delete_macro(ip, params):
    '''Makes /ir_delete_macro API call to requested IP, returns response.
    Requires existing macro name argument.
    '''
    return asyncio.run(request(ip, ['ir_delete_macro', params[0]]))


@add_endpoint("ir_save_macros")
def ir_save_macros(ip, _):
    '''Makes /ir_save_macros API call to requested IP, returns response.'''
    return asyncio.run(request(ip, ['ir_save_macros']))


@add_endpoint("ir_add_macro_action")
@requires_params
def ir_add_macro_action(ip, params):
    '''Makes /ir_add_macro_action API call to requested IP, returns response.
    Requires existing macro name, IR target name, IR key name, delay (int, ms)
    and repeat (int, number of times to press key) arguments.
    '''
    if len(params) >= 3:
        return asyncio.run(request(ip, ['ir_add_macro_action', *params]))
    raise SyntaxError


@add_endpoint("ir_run_macro")
@requires_params
def ir_run_macro(ip, params):
    '''Makes /ir_run_macro API call to requested IP, returns response.
    Requires existing macro name argument.
    '''
    return asyncio.run(request(ip, ['ir_run_macro', params[0]]))


@add_endpoint("get_temp")
def get_temp(ip, _):
    '''Makes /get_temp API call to requested IP, returns response.'''
    return asyncio.run(request(ip, ['get_temp']))


@add_endpoint("get_humid")
def get_humid(ip, _):
    '''Makes /get_humid API call to requested IP, returns response.'''
    return asyncio.run(request(ip, ['get_humid']))


@add_endpoint("get_climate")
def get_climate(ip, _):
    '''Makes /get_climate API call to requested IP, returns response.'''
    return asyncio.run(request(ip, ['get_climate_data']))


@add_endpoint("clear_log")
def clear_log(ip, _):
    '''Makes /clear_log API call to requested IP, returns response.'''
    return asyncio.run(request(ip, ['clear_log']))


@add_endpoint("condition_met")
@requires_params
@requires_sensor("Must specify sensor")
def condition_met(ip, target, _):
    '''Makes /condition_met API call to requested IP, returns response.
    Requires sensor ID argument.
    '''
    return asyncio.run(request(ip, ['condition_met', target]))


@add_endpoint("trigger_sensor")
@requires_params
@requires_sensor("Must specify sensor")
def trigger_sensor(ip, target, _):
    '''Makes /trigger_sensor API call to requested IP, returns response.
    Requires sensor ID argument.
    '''
    return asyncio.run(request(ip, ['trigger_sensor', target]))


@add_endpoint("turn_on")
@requires_params
@requires_device("Can only turn on/off devices, use enable/disable for sensors")
def turn_on(ip, target, _):
    '''Makes /turn_on API call to requested IP, returns response.
    Requires device ID argument.
    '''
    return asyncio.run(request(ip, ['turn_on', target]))


@add_endpoint("turn_off")
@requires_params
@requires_device("Can only turn on/off devices, use enable/disable for sensors")
def turn_off(ip, target, _):
    '''Makes /turn_off API call to requested IP, returns response.
    Requires device ID argument.
    '''
    return asyncio.run(request(ip, ['turn_off', target]))


@add_endpoint("set_gps_coords")
@requires_params
def set_gps_coords(ip, params):
    '''Makes /set_gps_coords API call to requested IP, returns response.
    Requires device ID argument.
    Requires latitude and longitude arguments (float).
    '''
    if len(params) >= 2:
        payload = {'latitude': params[0], 'longitude': params[1]}
        return asyncio.run(request(ip, ['set_gps_coords', payload]))
    raise SyntaxError


@add_endpoint("load_cell_tare")
@requires_params
@requires_sensor("Must specify load cell sensor")
def load_cell_tare(ip, target, _):
    '''Makes /load_cell_tare API call to requested IP, returns response.
    Requires load cell sensor ID argument.
    '''
    return asyncio.run(request(ip, ['load_cell_tare', target]))


@add_endpoint("load_cell_read")
@requires_params
@requires_sensor("Must specify load cell sensor")
def load_cell_get_raw_reading(ip, target, _):
    '''Makes /load_cell_read API call to requested IP, returns response.
    Requires load cell sensor ID argument.
    '''
    return asyncio.run(request(ip, ['load_cell_read', target]))
