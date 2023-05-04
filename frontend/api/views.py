from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse, FileResponse
from django.template import loader
from django.views.decorators.csrf import ensure_csrf_cookie
import json
import asyncio
import re

from node_configuration.models import Node
from node_configuration.get_api_target_menu_options import get_api_target_menu_options
from api.models import Macro

# Used to determine if keyword or timestamp schedule rule
timestamp_regex = r'^([0-1][0-9]|2[0-3]):[0-5][0-9]$'


# Receives schedule params in post, renders rule_modal template
def edit_rule(request):
    if request.method == "POST":
        data = json.loads(request.body.decode("utf-8"))
    else:
        return render(request, 'api/rule_modal.html')

    if data['rule'].startswith('fade'):
        data['fade'] = True
        data['duration'] = data['rule'].split('/')[2]
        data['rule'] = data['rule'].split('/')[1]

    if len(data['timestamp']) == 0 or re.match(timestamp_regex, data['timestamp']):
        data['show_timestamp'] = True
    else:
        data['show_timestamp'] = False

    print(data)

    return render(request, 'api/rule_modal.html', data)



def legacy_api(request):
    context = []

    for i in Node.objects.all():
        context.append(i)

    template = loader.get_template('api/legacy_api.html')

    return HttpResponse(template.render({'context': context}, request))



def get_status(request, node):
    ip = Node.objects.get(friendly_name = node).ip

    try:
        status = parse_command(ip, ["status"])
    except OSError:
        return JsonResponse("Error: Unable to connect.", safe=False, status=502)

    return JsonResponse(status, safe=False, status=200)



@ensure_csrf_cookie
def api_overview(request, recording=False, start=False):
    rooms = {}

    for i in Node.objects.all():
        if i.floor in rooms.keys():
            rooms[i.floor].append(i)
        else:
            rooms[i.floor] = [i]

    context = {}
    context['nodes'] = {}
    context['macros'] = {}

    floors = list(rooms.keys())
    floors.sort()

    # Sort by floor number
    for floor in floors:
        context['nodes'][floor] = rooms[floor]

    for macro in Macro.objects.all():
        context['macros'][macro.name] = json.loads(macro.actions)

    if recording:
        context['recording'] = recording

        # Block instructions popup if cookie set
        if request.COOKIES.get('skip_instructions'):
            context['skip_instructions'] = True

    if start:
        # Show instructions popup (unless cookie set)
        context['start_recording'] = True

    return render(request, 'api/overview.html', context)


@ensure_csrf_cookie
def api(request, node, recording=False):
    target = Node.objects.get(friendly_name = node)

    try:
        status = parse_command(target.ip, ["status"])
        if status == "Error: Request timed out":
            raise OSError

    # Render connection failed page
    except OSError:
        context = {"ip": target.ip, "id": target.friendly_name}
        template = loader.get_template('api/unable_to_connect.html')
        return HttpResponse(template.render({'context': context}, request))

    # If ApiTarget configured, add all valid options for target IP so user can change rule
    if "api-target" in str(status):
        status["api_target_options"] = {}

        # Get object containing all valid options for all nodes
        options = get_api_target_menu_options(target.friendly_name)

        # Get target IP(s) from config file, use to find correct options in object above
        config = target.config.config

        for i in config:
            if i.startswith("device") and config[i]['type'] == 'api-target':
                # ApiTarget found, find section in options object with matching IP, add to context
                for node in options['addresses']:
                    if options['addresses'][node] == config[i]['ip']:
                        status["api_target_options"][i] = options[node]
                        break

                # JSON-encode rule dicts
                status['devices'][i]['current_rule'] = json.dumps(status['devices'][i]['current_rule'])

                for rule in status['devices'][i]['schedule']:
                    status['devices'][i]['schedule'][rule] = json.dumps(status['devices'][i]['schedule'][rule])

    template = loader.get_template('api/api_card.html')

    status["metadata"]["ip"] = target.ip

    # Add temp history chart to frontend if temp sensor present
    for i in status["sensors"]:
        if status["sensors"][i]['type'] == 'si7021':
            status["metadata"]["thermostat"] = True
            break

    if recording:
        status["metadata"]["recording"] = recording

    print(json.dumps(status, indent=4))

    return HttpResponse(template.render({'context': status}, request))



# TODO unused? Climate card updates from status object
def get_climate_data(request, node):
    ip = Node.objects.get(friendly_name = node).ip

    try:
        data = parse_command(ip, ["get_climate"])
    except OSError:
        return JsonResponse("Error: Unable to connect.", safe=False, status=502)

    return JsonResponse(data, safe=False, status=200)



def reboot_all(request):
    for node in Node.objects.all():
        try:
            print(f"Rebooting {node.friendly_name}...")
            response = parse_command(node.ip, ['reboot'])
            print("Done")
        except (ConnectionRefusedError, OSError):
            print(f"Unable to connect to {node.friendly_name}")

    return JsonResponse("Done", safe=False, status=200)



def reset_all(request):
    for node in Node.objects.all():
        try:
            response = parse_command(node.ip, ['reset_all_rules'])
            print(node.friendly_name)
            print(json.dumps(response, indent=4))
            print()
        except (ConnectionRefusedError, OSError):
            print(f"Unable to connect to {node.friendly_name}\n")

    return JsonResponse("Done", safe=False, status=200)



def send_command(request):
    if request.method == "POST":
        data = json.loads(request.body.decode("utf-8"))
    else:
        return JsonResponse({'Error': 'Must post data'}, safe=False, status=405)

    if re.match("^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$", data["target"]):
        # New API Card interface
        ip = data["target"]
    else:
        # Legacy API
        ip = Node.objects.get(friendly_name = data["target"]).ip

    cmd = data["command"]
    del data["target"], data["command"]
    args = [cmd]

    for i in data:
        args.append(data[i].strip())

    print("\n" + ip + "\n" + str(args) + "\n")

    try:
        response = parse_command(ip, args)
    except OSError:
        return JsonResponse("Error: Unable to connect.", safe=False, status=502)

    if cmd == "disable" and len(data["delay_input"]) > 0:
        args.insert(0, "enable_in")
        print(ip + "\n" + str(args) + "\n")
        parse_command(ip, args)
    elif cmd == "enable" and len(data["delay_input"]) > 0:
        args.insert(0, "disable_in")
        print(ip + "\n" + str(args) + "\n")
        parse_command(ip, args)

    return JsonResponse(response, safe=False, status=200)



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
        res = await reader.read()
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



def run_macro(request, name):
    try:
        macro = Macro.objects.get(name = name)
    except Macro.DoesNotExist:
        return JsonResponse(f"Error: Macro {name} does not exist.", safe=False, status=404)

    actions = json.loads(macro.actions)
    for action in actions:
        parse_command(action['ip'], action['args'])

    return JsonResponse("Done", safe=False, status=200)



def add_macro_action(request):
    if request.method == "POST":
        data = json.loads(request.body.decode("utf-8"))
    else:
        return JsonResponse({'Error': 'Must post data'}, safe=False, status=405)

    try:
        macro = Macro.objects.get(name = data['name'])
    except Macro.DoesNotExist:
        macro = Macro.objects.create(name = data['name'])

    try:
        macro.add_action(data['action'])
    except (SyntaxError, KeyError):
        # Delete empty macro if failed to add first action
        if not len(json.loads(macro.actions)):
            macro.delete()
        return JsonResponse("Invalid action", safe=False, status=400)

    print(f"Added action: {data['action']}")

    return JsonResponse("Done", safe=False, status=200)



def edit_macro(request, name):
    try:
        macro = Macro.objects.get(name = name)
    except Macro.DoesNotExist:
        return JsonResponse(f"Error: Macro {name} does not exist.", safe=False, status=404)

    template = loader.get_template('api/edit_modal.html')

    context = {'name': name, 'actions': json.loads(macro.actions)}

    return HttpResponse(template.render(context, request))



def delete_macro(request, name):
    try:
        macro = Macro.objects.get(name = name)
    except Macro.DoesNotExist:
        return JsonResponse(f"Error: Macro {name} does not exist.", safe=False, status=404)

    macro.delete()

    return JsonResponse("Done", safe=False, status=200)



def delete_macro_action(request, name, index):
    try:
        macro = Macro.objects.get(name = name)
    except Macro.DoesNotExist:
        return JsonResponse(f"Error: Macro {name} does not exist.", safe=False, status=404)

    try:
        macro.del_action(index)
    except ValueError:
        return JsonResponse("ERROR: Macro action does not exist.", safe=False, status=404)

    return JsonResponse("Done", safe=False, status=200)



def macro_name_available(request, name):
    try:
        macro = Macro.objects.get(name = name)
    except Macro.DoesNotExist:
        return JsonResponse(f"Name {name} available.", safe=False, status=200)

    return JsonResponse(f"Name {name} already in use.", safe=False, status=409)



# Returns cookie to skip record macro instructions popup
def skip_instructions(request):
    response = HttpResponse()
    response.set_cookie('skip_instructions', 'true')
    return response



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

@add_endpoint("reset_all_rules")
def reset_all_rules(ip, params):
    return asyncio.run(request(ip, ['reset_all_rules']))

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
    # TODO iterate model
    elif len(params) > 0 and params[0] in ['sunrise', 'sunset']:
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
    # TODO iterate model
    elif len(params) > 0 and params[0] in ['sunrise', 'sunset']:
        timestamp = params.pop(0)
    else:
        return {"ERROR": "Must specify time (HH:MM) of rule to remove"}

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
        return {"ERROR" : "Please fill out all fields"}

    keyword = params.pop(0)

    if len(params) > 0 and re.match("^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$", params[0]):
        timestamp = params.pop(0)
    else:
        return {"ERROR": "Timestamp format must be HH:MM (no AM/PM)"}

    cmd = ['add_schedule_keyword', {keyword: timestamp}]

    return asyncio.run(request(ip, cmd))

@add_endpoint("remove_schedule_keyword")
def remove_schedule_keyword(ip, params):
    if len(params) == 0:
        return {"ERROR" : "Please fill out all fields"}

    cmd = ['remove_schedule_keyword', params.pop(0)]
    return asyncio.run(request(ip, cmd))

@add_endpoint("save_schedule_keywords")
def save_rules(ip, params):
    return asyncio.run(request(ip, ['save_schedule_keywords']))

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

@add_endpoint("get_climate")
def get_climate(ip, params):
    return asyncio.run(request(ip, ['get_climate_data']))

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
