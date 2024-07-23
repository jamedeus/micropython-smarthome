import json
import itertools
from functools import wraps
from concurrent.futures import ThreadPoolExecutor
from django.shortcuts import render
from django.http import HttpResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from node_configuration.views import requires_post, standard_response, error_response
from node_configuration.models import Node, ScheduleKeyword
from node_configuration.get_api_target_menu_options import get_api_target_menu_options
from Webrepl import Webrepl
from api.models import Macro
from api_endpoints import endpoint_map
from helper_functions import (
    is_device,
    get_schedule_keywords_dict,
    get_device_and_sensor_metadata
)


# Decorator looks up target node, returns error if does not exist
# Passes node model entry to wrapped function as second arg
def get_target_node(func):
    @wraps(func)
    def wrapper(request, node, **kwargs):
        try:
            node = Node.objects.get(friendly_name=node)
        except Node.DoesNotExist:
            return error_response(message=f'Node named {node} not found', status=404)
        return func(request, node, **kwargs)
    return wrapper


# Returns mapping dict with devices and sensors subdicts (types as keys)
# containing all relevant metadata (prompts, limits, triggerable sensors)
def get_metadata_map():
    # Get object containing metadata for all device and sensor types
    metadata = get_device_and_sensor_metadata()

    output = {'devices': {}, 'sensors': {}}

    # Add device config_name, rule_prompt, and rule_limits
    for i in metadata['devices']:
        name = i["config_name"]
        output['devices'][name] = {}
        output['devices'][name]['rule_prompt'] = i["rule_prompt"]
        if "rule_limits" in i.keys():
            output['devices'][name]['rule_limits'] = i["rule_limits"]

    # Add sensor config_name, rule_prompt, rule_limits, and triggerable bool
    for i in metadata['sensors']:
        name = i["config_name"]
        output['sensors'][name] = {}
        output['sensors'][name]['rule_prompt'] = i["rule_prompt"]
        if "rule_limits" in i.keys():
            output['sensors'][name]['rule_limits'] = i["rule_limits"]
        if "triggerable" in i.keys():
            output['sensors'][name]['triggerable'] = i["triggerable"]

    return output


@get_target_node
def get_status(request, node):
    # Query status object
    try:
        status = parse_command(node.ip, ["status"])
    except OSError:
        return error_response(message='Unable to connect', status=502)

    # Success if dict, error if string
    if isinstance(status, dict):
        return standard_response(message=status)
    else:
        return error_response(message=status, status=502)


@ensure_csrf_cookie
def api_overview(request, recording=False):
    rooms = {}

    for i in Node.objects.all():
        if i.floor in rooms.keys():
            rooms[i.floor].append(i.friendly_name)
        else:
            rooms[i.floor] = [i.friendly_name]

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

    print(json.dumps(context, indent=4))

    return render(request, 'api/overview.html', context)


# Takes Node, returns options for all api-target instances
def get_api_target_options(node):
    # Get object containing all valid options for all nodes
    options = get_api_target_menu_options(node.friendly_name)

    # Output will contain ApiTarget device IDs as keys, options as values
    output = {}

    # Find all api-target instances and add options for their target IP to output
    config = node.config.config
    for i in config:
        if is_device(i) and config[i]['_type'] == 'api-target':
            # Look up node matching api-target target IP
            target = Node.objects.get(ip=config[i]['ip'])
            if target == node:
                output[i] = options['self-target']
            else:
                output[i] = options[target.friendly_name]

    return output


@ensure_csrf_cookie
@get_target_node
def api(request, node, recording=False):
    # Get status object (used as context)
    try:
        status = parse_command(node.ip, ["status"])
        if str(status).startswith("Error: "):
            raise OSError

    # Render connection failed page
    except OSError:
        context = {"ip": node.ip, "id": node.friendly_name}
        return render(request, 'api/unable_to_connect.html', {'context': context})

    # Add target IP (used to send API calls to node)
    # Add name of macro being recorded (False if not recording)
    # Add metadata mapping dict (contains rule_prompt, limits, etc)
    context = {
        'status': status,
        'target_ip': node.ip,
        'recording': recording,
        'instance_metadata': get_metadata_map()
    }

    # If ApiTarget configured get options for ApiTargetRuleModal dropdowns
    if "api-target" in str(status):
        context['api_target_options'] = get_api_target_options(node)

    # If IR Blaster configured get IR macros
    if status['metadata']['ir_blaster']:
        context['ir_macros'] = parse_command(node.ip, ["ir_get_existing_macros"])

    print(json.dumps(context, indent=4))
    return render(request, 'api/api_card.html', context)


# TODO unused? Climate card updates from status object
@get_target_node
def get_climate_data(request, node):
    try:
        data = parse_command(node.ip, ["get_climate"])
    except OSError:
        return error_response(message='Unable to connect', status=502)

    return standard_response(message=data)


def reboot_all(request):
    print('Rebooting all nodes:')

    # Call parse_command(node.ip, ['reboot']) for all nodes in parallel
    actions = [(node, ['reboot']) for node in Node.objects.all()]
    with ThreadPoolExecutor(max_workers=20) as executor:
        for result in executor.map(parse_command_wrapper, *zip(*actions)):
            print(json.dumps(result, indent=4))

    return standard_response(message='Done')


def reset_all(request):
    print('Reseting all rules:')

    # Call parse_command(node.ip, ['reset_all_rules']) for all nodes in parallel
    actions = [(node, ['reset_all_rules']) for node in Node.objects.all()]
    with ThreadPoolExecutor(max_workers=20) as executor:
        for result in executor.map(parse_command_wrapper, *zip(*actions)):
            print(json.dumps(result, indent=4))

    return standard_response(message='Done')


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

    return standard_response(message='Done')


# Receives node IP, overwrites node config with current schedule rules, updates config in backend database
# Called when user clicks yes on toast notification after modifying schedule rules
@requires_post
def sync_schedule_rules(data):
    try:
        node = Node.objects.get(ip=data['ip'])
    except Node.DoesNotExist:
        return error_response(message=f"Node with IP {data['ip']} not found", status=404)

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

        return standard_response('Done syncing schedule rules')
    else:
        return error_response(message='Failed to save rules', status=500)


@requires_post
def send_command(data):
    # Get target node IP and API endpoint
    ip = data["target"]
    cmd = data["command"]
    del data["target"], data["command"]

    # Add endpoint (must be first) followed by remaining args
    args = [cmd]
    for param in data.values():
        # Remove extra whitespace from strings
        if type(param) is str:
            args.append(param.strip())
        # Stringify objects (eg api-target rule)
        elif type(param) in (dict, list):
            args.append(json.dumps(param))
        else:
            args.append(param)

    print(f"\nsend_command: {ip}: {str(args)}")

    try:
        response = parse_command(ip, args)
    except OSError:
        return error_response(message='Unable to connect', status=502)

    return standard_response(message=response)


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
        return "Error: Missing required parameters"
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
        return error_response(message=f'Macro {name} does not exist', status=404)

    # List of 2-item tuples containing ip, arg list for each action
    # example: ('192.168.1.246', ['disable', 'device2'])
    actions = [(action['ip'], action['args']) for action in json.loads(macro.actions)]

    # Run all actions in parallel
    with ThreadPoolExecutor(max_workers=20) as executor:
        executor.map(parse_command, *zip(*actions))

    return standard_response(message='Done')


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
        return error_response('Invalid action', status=400)

    print(f"Added action: {data['action']}")

    return standard_response(message='Done')


def delete_macro(request, name):
    try:
        macro = Macro.objects.get(name=name)
    except Macro.DoesNotExist:
        return error_response(message=f'Macro {name} does not exist', status=404)

    macro.delete()

    return standard_response(message='Done')


def delete_macro_action(request, name, index):
    try:
        macro = Macro.objects.get(name=name)
    except Macro.DoesNotExist:
        return error_response(message=f'Macro {name} does not exist', status=404)

    try:
        macro.del_action(index)
    except ValueError:
        return error_response(message='Macro action does not exist', status=404)

    return standard_response(message='Done')


def macro_name_available(request, name):
    try:
        Macro.objects.get(name=name)
        return error_response(message=f'Name {name} already in use', status=409)
    except Macro.DoesNotExist:
        return standard_response(message=f'Name {name} available')


def get_macro_actions(request, name):
    try:
        macro = Macro.objects.get(name=name)
        return standard_response(message=json.loads(macro.actions))
    except Macro.DoesNotExist:
        return error_response(message=f'Macro {name} does not exist', status=404)


# Returns cookie to skip record macro instructions popup
def skip_instructions(request):
    response = HttpResponse()
    response.set_cookie('skip_instructions', 'true')
    return response


@requires_post
def edit_ir_macro(data):
    ip = data['ip']
    macro_name = data['name']

    # Delete existing macro, create empty macro with same name
    parse_command(ip, ['ir_delete_macro', macro_name])
    parse_command(ip, ['ir_create_macro', macro_name])

    # Add each macro action
    for action in data['actions']:
        payload = ['ir_add_macro_action', macro_name]
        payload.extend(action.split(' '))
        parse_command(ip, payload)

    # Save changes
    parse_command(ip, ['ir_save_macros'])

    return standard_response(message='Done')


@requires_post
def add_ir_macro(data):
    ip = data['ip']
    macro_name = data['name']

    # Create new macro
    parse_command(ip, ['ir_create_macro', macro_name])

    # Add each action
    for action in data['actions']:
        payload = ['ir_add_macro_action', macro_name]
        payload.extend(action.split(' '))
        parse_command(ip, payload)

    # Save changes
    parse_command(ip, ['ir_save_macros'])

    return standard_response(message='Done')
