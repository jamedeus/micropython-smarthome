import json
import itertools
from concurrent.futures import ThreadPoolExecutor
from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from node_configuration.views import requires_post
from node_configuration.models import Node, ScheduleKeyword
from node_configuration.get_api_target_menu_options import get_api_target_menu_options
from helper_functions import valid_ip, valid_timestamp, is_device, get_schedule_keywords_dict
from Webrepl import Webrepl
from api.models import Macro
from api_endpoints import endpoint_map


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

    if len(data['timestamp']) == 0 or valid_timestamp(data['timestamp']):
        data['show_timestamp'] = True
    else:
        data['show_timestamp'] = False

    # Add schedule keywords
    data['schedule_keywords'] = get_schedule_keywords_dict()

    print(data)

    return render(request, 'api/rule_modal.html', data)


def legacy_api(request):
    context = [node for node in Node.objects.all()]
    return render(request, 'api/legacy_api.html', {'context': context})


def get_status(request, node):
    try:
        ip = Node.objects.get(friendly_name=node).ip
    except Node.DoesNotExist:
        return JsonResponse({"Error": f"Node named {node} not found"}, safe=False, status=404)

    # Query status object
    try:
        status = parse_command(ip, ["status"])
    except OSError:
        return JsonResponse("Error: Unable to connect.", safe=False, status=502)

    # Success if dict, error if string
    if isinstance(status, dict):
        return JsonResponse(status, safe=False, status=200)
    else:
        return JsonResponse(status, safe=False, status=502)


@ensure_csrf_cookie
def api_overview(request, recording=False, start=False):
    rooms = {}

    for i in Node.objects.all():
        if i.floor in rooms.keys():
            rooms[i.floor].append(i)
        else:
            rooms[i.floor] = [i]

    context = {
        'nodes': {},
        'macros': {}
    }

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


# Takes Node, returns options for all api-target instances
def get_api_target_instance_options(node, status):
    # Get object containing all valid options for all nodes
    options = get_api_target_menu_options(node.friendly_name)

    # Get target IP(s) of each api-target instance from config file
    # Used as keys in options['addresses'] (above)
    config = node.config.config

    # Find all api-target instances, find same instance in options object, add options to output
    for i in config:
        if is_device(i) and config[i]['_type'] == 'api-target':
            # Find section in options object with matching IP, add to context
            for node in options['addresses']:
                if options['addresses'][node] == config[i]['ip']:
                    status["api_target_options"][i] = options[node]
                    break

            # JSON-encode rule dicts
            status['devices'][i]['current_rule'] = json.dumps(status['devices'][i]['current_rule'])
            for rule in status['devices'][i]['schedule']:
                status['devices'][i]['schedule'][rule] = json.dumps(status['devices'][i]['schedule'][rule])

    return status


@ensure_csrf_cookie
def api(request, node, recording=False):
    try:
        target = Node.objects.get(friendly_name=node)
    except Node.DoesNotExist:
        return JsonResponse({"Error": f"Node named {node} not found"}, safe=False, status=404)

    try:
        status = parse_command(target.ip, ["status"])
        if str(status).startswith("Error: "):
            raise OSError

    # Render connection failed page
    except OSError:
        context = {"ip": target.ip, "id": target.friendly_name}
        return render(request, 'api/unable_to_connect.html', {'context': context})

    # Add IP, parsed into target_node var on frontend
    status["metadata"]["ip"] = target.ip

    # If ApiTarget configured, add options for all valid API commands for current target IP
    if "api-target" in str(status):
        status["api_target_options"] = {}
        status = get_api_target_instance_options(target, status)

    # Add temp history chart to frontend if temp sensor present
    for i in status["sensors"]:
        if status["sensors"][i]['type'] == 'si7021':
            status["metadata"]["thermostat"] = True
            break

    if recording:
        status["metadata"]["recording"] = recording

    print(json.dumps(status, indent=4))

    return render(request, 'api/api_card.html', {'context': status})


# TODO unused? Climate card updates from status object
def get_climate_data(request, node):
    try:
        ip = Node.objects.get(friendly_name=node).ip
    except Node.DoesNotExist:
        return JsonResponse({"Error": f"Node named {node} not found"}, safe=False, status=404)

    try:
        data = parse_command(ip, ["get_climate"])
    except OSError:
        return JsonResponse("Error: Unable to connect.", safe=False, status=502)

    return JsonResponse(data, safe=False, status=200)


def reboot_all(request):
    print('Rebooting all nodes:')

    # Call parse_command(node.ip, ['reboot']) for all nodes in parallel
    actions = [(node, ['reboot']) for node in Node.objects.all()]
    with ThreadPoolExecutor(max_workers=20) as executor:
        for result in executor.map(parse_command_wrapper, *zip(*actions)):
            print(json.dumps(result, indent=4))

    return JsonResponse("Done", safe=False, status=200)


def reset_all(request):
    print('Reseting all rules:')

    # Call parse_command(node.ip, ['reset_all_rules']) for all nodes in parallel
    actions = [(node, ['reset_all_rules']) for node in Node.objects.all()]
    with ThreadPoolExecutor(max_workers=20) as executor:
        for result in executor.map(parse_command_wrapper, *zip(*actions)):
            print(json.dumps(result, indent=4))

    return JsonResponse("Done", safe=False, status=200)


# Receives node IP and existing schedule keywords in post body
# Uploads missing keywords (if any) from database
@requires_post
def sync_schedule_keywords(data):
    # Get current keywords from database, target node
    database = get_schedule_keywords_dict()
    node = data['existing_keywords']

    # Get all schedule keywords missing from target node
    missing = list(ScheduleKeyword.objects.exclude(keyword__in=node.keys()))

    # Get all schedule keywords deleted from database that still exist on target node
    deleted = [keyword for keyword in node.keys() if keyword not in database.keys()]

    # Get all schedule keywords with different timestamps
    modified = [keyword for keyword in node if keyword not in deleted and database[keyword] != node[keyword]]
    modified = [ScheduleKeyword.objects.get(keyword=i) for i in modified if i not in ['sunrise', 'sunset']]

    # Add all missing keywords, overwrite all modified keywords
    for keyword in itertools.chain(missing, modified):
        parse_command(data['ip'], ['add_schedule_keyword', keyword.keyword, keyword.timestamp])

    # Remove all deleted keywords
    for keyword in deleted:
        parse_command(data['ip'], ['remove_schedule_keyword', keyword])

    # Print status messages
    if len(missing):
        print(f"Added {len(missing)} missing schedule keywords")
    if len(modified):
        print(f"Updated {len(modified)} outdated schedule keywords")
    if len(deleted):
        print(f"Deleted {len(deleted)} schedule keywords that no longer exist in database")

    # Save changes (if any) to disk on target node
    if len(missing) or len(modified) or len(deleted):
        parse_command(data['ip'], ['save_schedule_keywords'])

    return JsonResponse("Done", safe=False, status=200)


# Receives node IP, overwrites node config with current schedule rules, updates config in backend database
# Called when user clicks yes on toast notification after modifying schedule rules
@requires_post
def sync_schedule_rules(data):
    try:
        node = Node.objects.get(ip=data['ip'])
    except Node.DoesNotExist:
        return JsonResponse({"Error": f"Node with IP {data['ip']} not found"}, safe=False, status=404)

    # Save schedule rules to disk on node
    response = parse_command(node.ip, ['save_rules'])
    if isinstance(response, dict):
        # Open webrepl connection, download config.json
        webrepl = Webrepl(node.ip)
        webrepl.open_connection()
        config_file = webrepl.get_file_mem('config.json')
        webrepl.close_connection()

        # Overwrite config in database, write config to disk
        node.config.config = json.loads(config_file)
        node.config.save()
        node.config.write_to_disk()

        return JsonResponse("Done syncing schedule rules", safe=False, status=200)
    else:
        return JsonResponse({"Error": "Failed to save rules"}, safe=False, status=500)


@requires_post
def send_command(data):
    if valid_ip(data["target"]):
        # New API Card interface
        ip = data["target"]
    else:
        # Legacy API
        try:
            ip = Node.objects.get(friendly_name=data["target"]).ip
        except Node.DoesNotExist:
            return JsonResponse({"Error": f"Node named {data['target']} not found"}, safe=False, status=404)

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


# Takes target IP + args list (first item must be endpoint name)
# Find endpoint matching first arg, call handler function with remaining args
def parse_command(ip, args):
    if len(args) == 0:
        return "Error: No command received"

    endpoint = args[0]
    args = args[1:]

    try:
        return endpoint_map[endpoint](ip, args)
    except SyntaxError:
        return {"ERROR": "Please fill out all fields"}
    except KeyError:
        return "Error: Command not found"


# Takes node instead of IP, returns JSON-printable dict with response
# Used by bulk command endpoints (reboot_all, reset_all_rules, etc)
def parse_command_wrapper(node, args):
    response = parse_command(node.ip, args)
    return {
        'node': node.friendly_name,
        'response': response
    }


def run_macro(request, name):
    try:
        macro = Macro.objects.get(name=name)
    except Macro.DoesNotExist:
        return JsonResponse(f"Error: Macro {name} does not exist.", safe=False, status=404)

    # List of 2-item tuples containing ip, arg list for each action
    # example: ('192.168.1.246', ['disable', 'device2'])
    actions = [(action['ip'], action['args']) for action in json.loads(macro.actions)]

    # Run all actions in parallel
    with ThreadPoolExecutor(max_workers=20) as executor:
        executor.map(parse_command, *zip(*actions))

    return JsonResponse("Done", safe=False, status=200)


@requires_post
def add_macro_action(data):
    try:
        macro = Macro.objects.get(name=data['name'])
    except Macro.DoesNotExist:
        macro = Macro.objects.create(name=data['name'])

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
        macro = Macro.objects.get(name=name)
    except Macro.DoesNotExist:
        return JsonResponse(f"Error: Macro {name} does not exist.", safe=False, status=404)

    context = {'name': name, 'actions': json.loads(macro.actions)}
    return render(request, 'api/edit_modal.html', context)


def delete_macro(request, name):
    try:
        macro = Macro.objects.get(name=name)
    except Macro.DoesNotExist:
        return JsonResponse(f"Error: Macro {name} does not exist.", safe=False, status=404)

    macro.delete()

    return JsonResponse("Done", safe=False, status=200)


def delete_macro_action(request, name, index):
    try:
        macro = Macro.objects.get(name=name)
    except Macro.DoesNotExist:
        return JsonResponse(f"Error: Macro {name} does not exist.", safe=False, status=404)

    try:
        macro.del_action(index)
    except ValueError:
        return JsonResponse("ERROR: Macro action does not exist.", safe=False, status=404)

    return JsonResponse("Done", safe=False, status=200)


def macro_name_available(request, name):
    try:
        Macro.objects.get(name=name)
        return JsonResponse(f"Name {name} already in use.", safe=False, status=409)
    except Macro.DoesNotExist:
        return JsonResponse(f"Name {name} available.", safe=False, status=200)


# Returns cookie to skip record macro instructions popup
def skip_instructions(request):
    response = HttpResponse()
    response.set_cookie('skip_instructions', 'true')
    return response
