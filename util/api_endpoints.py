import json
import asyncio
from helper_functions import valid_timestamp, is_device_or_sensor, is_device, is_sensor, get_schedule_keywords_dict

# Valid IR commands for each target, used in error message
ir_commands = {
    "tv": "power, vol_up, vol_down, mute, up, down, left, right, enter, settings, exit, source",
    "ac": "ON, OFF, UP, DOWN, FAN, TIMER, UNITS, MODE, STOP, START"
}

# Populated with endpoint:handler pairs by decorators below
endpoints = []


def add_endpoint(url):
    def _add_endpoint(func):
        endpoints.append((url, func))
        return func
    return _add_endpoint


# Send JSON api request to node
async def request(ip, msg):
    # Open connection (5 second timeout)
    try:
        reader, writer = await asyncio.wait_for(asyncio.open_connection(ip, 8123), timeout=5)
    except asyncio.TimeoutError:
        return "Error: Request timed out"
    except OSError:
        return "Error: Failed to connect"

    # Send message
    try:
        writer.write('{}\n'.format(json.dumps(msg)).encode())
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
def status(ip, params):
    return asyncio.run(request(ip, ['status']))


@add_endpoint("reboot")
def reboot(ip, params):
    return asyncio.run(request(ip, ['reboot']))


@add_endpoint("disable")
def disable(ip, params):
    if len(params) == 0:
        raise SyntaxError

    if is_device_or_sensor(params[0]):
        return asyncio.run(request(ip, ['disable', params[0]]))
    else:
        return {"ERROR": "Can only disable devices and sensors"}


@add_endpoint("disable_in")
def disable_in(ip, params):
    if len(params) == 0:
        raise SyntaxError

    if is_device_or_sensor(params[0]):
        target = params.pop(0)
        try:
            period = float(params[0])
            return asyncio.run(request(ip, ['disable_in', target, period]))
        except IndexError:
            return {"ERROR": "Please specify delay in minutes"}
    else:
        return {"ERROR": "Can only disable devices and sensors"}


@add_endpoint("enable")
def enable(ip, params):
    if len(params) == 0:
        raise SyntaxError

    if is_device_or_sensor(params[0]):
        return asyncio.run(request(ip, ['enable', params[0]]))
    else:
        return {"ERROR": "Can only enable devices and sensors"}


@add_endpoint("enable_in")
def enable_in(ip, params):
    if len(params) == 0:
        raise SyntaxError

    if is_device_or_sensor(params[0]):
        target = params.pop(0)
        try:
            period = float(params[0])
            return asyncio.run(request(ip, ['enable_in', target, period]))
        except IndexError:
            return {"ERROR": "Please specify delay in minutes"}
    else:
        return {"ERROR": "Can only enable devices and sensors"}


@add_endpoint("set_rule")
def set_rule(ip, params):
    if len(params) == 0:
        raise SyntaxError

    if is_device_or_sensor(params[0]):
        target = params.pop(0)
        try:
            return asyncio.run(request(ip, ['set_rule', target, params[0]]))
        except IndexError:
            return {"ERROR": "Must specify new rule"}
    else:
        return {"ERROR": "Can only set rules for devices and sensors"}


@add_endpoint("reset_rule")
def reset_rule(ip, params):
    if len(params) == 0:
        raise SyntaxError

    if is_device_or_sensor(params[0]):
        target = params.pop(0)
        return asyncio.run(request(ip, ['reset_rule', target]))
    else:
        return {"ERROR": "Can only set rules for devices and sensors"}


@add_endpoint("reset_all_rules")
def reset_all_rules(ip, params):
    return asyncio.run(request(ip, ['reset_all_rules']))


@add_endpoint("get_schedule_rules")
def get_schedule_rules(ip, params):
    if len(params) == 0:
        raise SyntaxError

    if is_device_or_sensor(params[0]):
        target = params.pop(0)
        return asyncio.run(request(ip, ['get_schedule_rules', target]))
    else:
        return {"ERROR": "Only devices and sensors have schedule rules"}


@add_endpoint("add_rule")
def add_schedule_rule(ip, params):
    if len(params) == 0:
        raise SyntaxError

    if is_device_or_sensor(params[0]):
        target = params.pop(0)
    else:
        return {"ERROR": "Only devices and sensors have schedule rules"}

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
def remove_rule(ip, params):
    if len(params) == 0:
        raise SyntaxError

    if is_device_or_sensor(params[0]):
        target = params.pop(0)
    else:
        return {"ERROR": "Only devices and sensors have schedule rules"}

    if len(params) > 0 and valid_timestamp(params[0]):
        timestamp = params.pop(0)
    elif len(params) > 0 and params[0] in get_schedule_keywords_dict().keys():
        timestamp = params.pop(0)
    else:
        return {"ERROR": 'Must specify timestamp (HH:MM) or keyword of rule to remove'}

    return asyncio.run(request(ip, ['remove_rule', target, timestamp]))


@add_endpoint("save_rules")
def save_rules(ip, params):
    return asyncio.run(request(ip, ['save_rules']))


@add_endpoint("get_schedule_keywords")
def get_schedule_keywords(ip, params):
    return asyncio.run(request(ip, ['get_schedule_keywords']))


@add_endpoint("add_schedule_keyword")
def add_schedule_keyword(ip, params):
    if len(params) == 0:
        raise SyntaxError

    keyword = params.pop(0)

    if len(params) > 0 and valid_timestamp(params[0]):
        timestamp = params.pop(0)
    else:
        return {"ERROR": "Timestamp format must be HH:MM (no AM/PM)"}

    cmd = ['add_schedule_keyword', {keyword: timestamp}]

    return asyncio.run(request(ip, cmd))


@add_endpoint("remove_schedule_keyword")
def remove_schedule_keyword(ip, params):
    if len(params) == 0:
        raise SyntaxError

    cmd = ['remove_schedule_keyword', params.pop(0)]
    return asyncio.run(request(ip, cmd))


@add_endpoint("save_schedule_keywords")
def save_schedule_keywords(ip, params):
    return asyncio.run(request(ip, ['save_schedule_keywords']))


@add_endpoint("get_attributes")
def get_attributes(ip, params):
    if len(params) == 0:
        raise SyntaxError

    if is_device_or_sensor(params[0]):
        target = params.pop(0)
        return asyncio.run(request(ip, ['get_attributes', target]))
    else:
        return {"ERROR": "Must specify device or sensor"}


@add_endpoint("ir")
def ir(ip, params):
    if len(params) > 0 and (params[0] == "tv" or params[0] == "ac"):
        target = params.pop(0)
        try:
            return asyncio.run(request(ip, ['ir_key', target, params[0]]))
        except IndexError:
            return {"ERROR": f"Must specify one of the following commands: {ir_commands[target]}"}

    elif len(params) > 0 and params[0] == "backlight":
        params.pop(0)
        try:
            if params[0] == "on" or params[0] == "off":
                return asyncio.run(request(ip, ['backlight', params[0]]))
            else:
                raise IndexError
        except IndexError:
            return {"ERROR": "Must specify 'on' or 'off'"}
    else:
        raise SyntaxError


@add_endpoint("get_temp")
def get_temp(ip, params):
    return asyncio.run(request(ip, ['get_temp']))


@add_endpoint("get_humid")
def get_humid(ip, params):
    return asyncio.run(request(ip, ['get_humid']))


@add_endpoint("get_climate")
def get_climate(ip, params):
    return asyncio.run(request(ip, ['get_climate_data']))


@add_endpoint("clear_log")
def clear_log(ip, params):
    return asyncio.run(request(ip, ['clear_log']))


@add_endpoint("condition_met")
def condition_met(ip, params):
    try:
        if is_sensor(params[0]):
            return asyncio.run(request(ip, ['condition_met', params[0]]))
        else:
            raise IndexError
    except IndexError:
        return {"ERROR": "Must specify sensor"}


@add_endpoint("trigger_sensor")
def trigger_sensor(ip, params):
    try:
        if is_sensor(params[0]):
            return asyncio.run(request(ip, ['trigger_sensor', params[0]]))
        else:
            raise IndexError
    except IndexError:
        return {"ERROR": "Must specify sensor"}


@add_endpoint("turn_on")
def turn_on(ip, params):
    try:
        if is_device(params[0]):
            return asyncio.run(request(ip, ['turn_on', params[0]]))
        else:
            raise IndexError
    except IndexError:
        return {"ERROR": "Can only turn on/off devices, use enable/disable for sensors"}


@add_endpoint("turn_off")
def turn_off(ip, params):
    try:
        if is_device(params[0]):
            return asyncio.run(request(ip, ['turn_off', params[0]]))
        else:
            raise IndexError
    except IndexError:
        return {"ERROR": "Can only turn on/off devices, use enable/disable for sensors"}
