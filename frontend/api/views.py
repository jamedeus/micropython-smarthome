from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponse, Http404, JsonResponse, FileResponse
from django.template import loader
import json
import asyncio
import re

from node_configuration.models import Node



def api_overview(request):
    context = []

    for i in Node.objects.all():
        context.append(i)

    template = loader.get_template('api/index.html')

    return HttpResponse(template.render({'context': context}, request))



def get_status(request, node):
    ip = Node.objects.get(friendly_name = node).ip

    try:
        status = parse_command(ip, ["status"])
    except OSError:
        return JsonResponse("Error: Unable to connect.", safe=False, status=200)

    return JsonResponse(status, safe=False, status=200)



def send_command(request):
    if request.method == "POST":
        data = json.loads(request.body.decode("utf-8"))
    else:
        raise Http404("ERROR: Must post data")

    ip = Node.objects.get(friendly_name = data["target"]).ip
    cmd = data["command"]
    del data["target"], data["command"]

    args = [cmd]

    for i in data:
        args.append(data[i])

    print()
    print(ip)
    print(args)
    print()

    try:
        response = parse_command(ip, args)
    except OSError:
        return JsonResponse("Error: Unable to connect.", safe=False, status=200)

    return JsonResponse(response, safe=False, status=200)


# Send JSON api request to node
async def request(ip, msg):
    reader, writer = await asyncio.open_connection(ip, 8123)
    try:
        writer.write('{}\n'.format(json.dumps(msg)).encode())
        await writer.drain()
        res = await reader.read(1000)
    except OSError:
        return "Error: Request failed"
    try:
        response = json.loads(res)
    except ValueError:
        return "Error: Unable to decode response"
    writer.close()
    await writer.wait_closed()

    return response



def parse_command(ip, args):
    if len(args) == 0:
        return "Error: No command received"

    for endpoint in endpoints:
        if args[0] == endpoint[0]:
            # Remove endpoint arg
            args.pop(0)
            # Send remaining args to handler function
            return endpoint[1](ip, args)

    else:
        return "Error: Command not found"



# Populated with endpoint:handler pairs by decorators below
endpoints = []

def add_endpoint(url):
    def _add_endpoint(func):
        endpoints.append((url, func))
        return func
    return _add_endpoint

@add_endpoint("status")
def status(ip, params):
    return asyncio.run(request(ip, ['status']))

@add_endpoint("reboot")
def reboot(ip, params):
    return asyncio.run(request(ip, ['reboot']))

@add_endpoint("disable")
def disable(ip, params):
    if len(params) == 0:
        return {"ERROR" : "Please fill out all fields"}

    if params[0].startswith("sensor") or params[0].startswith("device"):
        return asyncio.run(request(ip, ['disable', params[0]]))
    else:
        return {"ERROR" : "Can only disable devices and sensors"}

@add_endpoint("disable_in")
def disable_in(ip, params):
    if len(params) == 0:
        return {"ERROR" : "Please fill out all fields"}

    if params[0].startswith("sensor") or params[0].startswith("device"):
        target = params.pop(0)
        try:
            period = float(params[0])
            return asyncio.run(request(ip, ['disable_in', target, period]))
        except IndexError:
            return {"ERROR": "Please specify delay in minutes"}
    else:
        return {"ERROR": "Can only disable devices and sensors"}

@add_endpoint("enable")
def disable(ip, params):
    if len(params) == 0:
        return {"ERROR" : "Please fill out all fields"}

    if params[0].startswith("sensor") or params[0].startswith("device"):
        return asyncio.run(request(ip, ['enable', params[0]]))
    else:
        return {"ERROR" : "Can only enable devices and sensors"}

@add_endpoint("enable_in")
def enable_in(ip, params):
    if len(params) == 0:
        return {"ERROR" : "Please fill out all fields"}

    if params[0].startswith("sensor") or params[0].startswith("device"):
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
        return {"ERROR" : "Please fill out all fields"}

    if params[0].startswith("sensor") or params[0].startswith("device"):
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
        return {"ERROR" : "Please fill out all fields"}

    if params[0].startswith("sensor") or params[0].startswith("device"):
        target = params.pop(0)
        return asyncio.run(request(ip, ['reset_rule', target]))
    else:
        return {"ERROR": "Can only set rules for devices and sensors"}

@add_endpoint("get_schedule_rules")
def get_schedule_rules(ip, params):
    if len(params) == 0:
        return {"ERROR" : "Please fill out all fields"}

    if params[0].startswith("sensor") or params[0].startswith("device"):
        target = params.pop(0)
        return asyncio.run(request(ip, ['get_schedule_rules', target]))
    else:
        return {"ERROR": "Only devices and sensors have schedule rules"}

@add_endpoint("add_rule")
def add_schedule_rule(ip, params):
    if len(params) == 0:
        return {"ERROR" : "Please fill out all fields"}

    if params[0].startswith("sensor") or params[0].startswith("device"):
        target = params.pop(0)
    else:
        return {"ERROR": "Only devices and sensors have schedule rules"}

    if len(params) > 0 and re.match("^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$", params[0]):
        timestamp = params.pop(0)
    else:
        return {"ERROR": "Must specify time (HH:MM) followed by rule"}

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
        return {"ERROR" : "Please fill out all fields"}

    if params[0].startswith("sensor") or params[0].startswith("device"):
        target = params.pop(0)
    else:
        return {"ERROR": "Only devices and sensors have schedule rules"}

    if len(params) > 0 and re.match("^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$", params[0]):
        timestamp = params.pop(0)
    else:
        return {"ERROR": "Must specify time (HH:MM) followed by rule"}

    return asyncio.run(request(ip, ['remove_rule', target, timestamp]))

@add_endpoint("get_attributes")
def get_attributes(ip, params):
    if len(params) == 0:
        return {"ERROR" : "Please fill out all fields"}

    if params[0].startswith("sensor") or params[0].startswith("device"):
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
            if target == "tv":
                return {"ERROR": "Must speficy one of the following commands: power, vol_up, vol_down, mute, up, down, left, right, enter, settings, exit, source"}
            elif target == "ac":
                return {"ERROR": "Must speficy one of the following commands: ON, OFF, UP, DOWN, FAN, TIMER, UNITS, MODE, STOP, START"}

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
        return {"ERROR" : "Please fill out all fields"}

@add_endpoint("get_temp")
def get_temp(ip, params):
    return asyncio.run(request(ip, ['get_temp']))

@add_endpoint("get_humid")
def get_humid(ip, params):
    return asyncio.run(request(ip, ['get_humid']))

@add_endpoint("clear_log")
def clear_log(ip, params):
    return asyncio.run(request(ip, ['clear_log']))

@add_endpoint("condition_met")
def condition_met(ip, params):
    try:
        if params[0].startswith("sensor"):
            return asyncio.run(request(ip, ['condition_met', params[0]]))
        else:
            raise IndexError
    except IndexError:
        return {"ERROR": "Must specify sensor"}

@add_endpoint("trigger_sensor")
def trigger_sensor(ip, params):
    try:
        if params[0].startswith("sensor"):
            return asyncio.run(request(ip, ['trigger_sensor', params[0]]))
        else:
            raise IndexError
    except IndexError:
        return {"ERROR": "Must specify sensor"}

@add_endpoint("turn_on")
def turn_on(ip, params):
    try:
        if params[0].startswith("device"):
            return asyncio.run(request(ip, ['turn_on', params[0]]))
        else:
            raise IndexError
    except IndexError:
        return {"ERROR": "Can only turn on/off devices, use enable/disable for sensors"}

@add_endpoint("turn_off")
def turn_on(ip, params):
    try:
        if params[0].startswith("device"):
            return asyncio.run(request(ip, ['turn_off', params[0]]))
        else:
            raise IndexError
    except IndexError:
        return {"ERROR": "Can only turn on/off devices, use enable/disable for sensors"}
