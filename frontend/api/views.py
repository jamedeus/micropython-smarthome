'''Django API endpoint functions used to control ESP32 nodes'''

import json
import itertools
from functools import wraps
from concurrent.futures import ThreadPoolExecutor
from django.shortcuts import render
from django.http import HttpResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from Webrepl import Webrepl
from api_endpoints import endpoint_map
from helper_functions import (
    is_device,
    get_schedule_keywords_dict,
    get_device_and_sensor_metadata
)
from node_configuration.views import requires_post, standard_response, error_response
from node_configuration.models import Node, ScheduleKeyword
from node_configuration.get_api_target_menu_options import get_api_target_menu_options
from api.models import Macro


def get_target_node(func):
    '''Decorator looks up target node, returns error if does not exist
    Passes node model entry to wrapped function as second arg
    '''
    @wraps(func)
    def wrapper(request, node, **kwargs):
        try:
            node = Node.objects.get(friendly_name=node)
        except Node.DoesNotExist:
            return error_response(message=f'Node named {node} not found', status=404)
        return func(request, node, **kwargs)
    return wrapper


def get_metadata_map():
    '''Returns mapping dict with devices and sensors subdicts (types as keys)
    containing all relevant metadata (prompts, limits, triggerable sensors)
    '''

    # Get dict with contents of all device and sensor metadata files
    metadata = get_device_and_sensor_metadata()

    output = {'devices': {}, 'sensors': {}}

    # Add device config_name, rule_prompt, and rule_limits
    for _type, value in metadata['devices'].items():
        output['devices'][_type] = {}
        output['devices'][_type]['rule_prompt'] = value['rule_prompt']
        if 'rule_limits' in value.keys():
            output['devices'][_type]['rule_limits'] = value['rule_limits']

    # Add sensor config_name, rule_prompt, rule_limits, and triggerable bool
    for _type, value in metadata['sensors'].items():
        output['sensors'][_type] = {}
        output['sensors'][_type]['rule_prompt'] = value['rule_prompt']
        output['sensors'][_type]['triggerable'] = value['triggerable']
        if 'rule_limits' in value.keys():
            output['sensors'][_type]['rule_limits'] = value['rule_limits']

    return output


@get_target_node
def get_status(request, node):
    '''Requests status object from ESP32 node and returns.
    Called by API card interface every 5 seconds to update state.
    '''

    # Query status object
    try:
        status = parse_command(node.ip, ["status"])
    except OSError:
        return error_response(message='Unable to connect', status=502)

    # Success if dict, error if string
    if isinstance(status, dict):
        return standard_response(message=status)

    return error_response(message=status, status=502)


@get_target_node
def get_log(request, node):
    '''Downloads requested node log file with webrepl and returns to client.'''

    try:
        webrepl = Webrepl(node.ip)
        log_file = webrepl.get_file_mem('app.log')
        webrepl.close_connection()
        return standard_response(message=log_file.decode())
    except OSError:
        return error_response(message="Failed to download log", status=502)


@ensure_csrf_cookie
def api_overview(request, recording=False):
    '''Renders the API overview page'''

    rooms = {}

    for i in Node.objects.all():
        if i.floor in rooms:
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


def get_api_target_options(node):
    '''Takes Node, returns options for all api-target instances'''

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
    '''Renders the API card interface for the requested ESP32 node'''

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


def reboot_all(request):
    '''Sends reboot API command to all ESP32 nodes in parallel.
    Called when "Reboot all" dropdown option on overview is clicked.
    '''
    print('Rebooting all nodes:')

    # Call parse_command(node.ip, ['reboot']) for all nodes in parallel
    actions = [(node, ['reboot']) for node in Node.objects.all()]
    with ThreadPoolExecutor(max_workers=20) as executor:
        for result in executor.map(parse_command_wrapper, *zip(*actions)):
            print(json.dumps(result, indent=4))

    return standard_response(message='Done')


def reset_all(request):
    '''Sends reset_all_rules API command to all ESP32 nodes in parallel.
    Called when "Reset all rules" dropdown option on overview is clicked.
    '''
    print('Reseting all rules:')

    # Call parse_command(node.ip, ['reset_all_rules']) for all nodes in parallel
    actions = [(node, ['reset_all_rules']) for node in Node.objects.all()]
    with ThreadPoolExecutor(max_workers=20) as executor:
        for result in executor.map(parse_command_wrapper, *zip(*actions)):
            print(json.dumps(result, indent=4))

    return standard_response(message='Done')


@requires_post
def sync_schedule_keywords(data):
    '''
    Receives node IP and existing schedule keywords in post body.
    Uploads missing keywords (if any) from database.
    '''

    # Get current keywords from database, target node
    database = get_schedule_keywords_dict()
    node = data['existing_keywords']

    # Get all schedule keywords missing from target node
    missing = list(ScheduleKeyword.objects.exclude(keyword__in=node.keys()))

    # Get all schedule keywords deleted from database that still exist on target node
    deleted = [keyword for keyword in node.keys() if keyword not in database.keys()]

    # Get all schedule keywords with different timestamps
    modified = [keyword for keyword in node
                if keyword not in deleted and database[keyword] != node[keyword]]
    modified = [ScheduleKeyword.objects.get(keyword=i) for i in modified
                if i not in ['sunrise', 'sunset']]

    # Add all missing keywords, overwrite all modified keywords
    for keyword in itertools.chain(missing, modified):
        parse_command(data['ip'], ['add_schedule_keyword', keyword.keyword, keyword.timestamp])

    # Remove all deleted keywords
    for keyword in deleted:
        parse_command(data['ip'], ['remove_schedule_keyword', keyword])

    # Print status messages for each category with 1 or more item
    if missing:
        print(f"Added {len(missing)} missing schedule keywords")
    if modified:
        print(f"Updated {len(modified)} outdated schedule keywords")
    if deleted:
        print(f"Deleted {len(deleted)} schedule keywords that no longer exist in database")

    # Save changes (if any) to disk on target node
    if missing or modified or deleted:
        parse_command(data['ip'], ['save_schedule_keywords'])

    return standard_response(message='Done')


@requires_post
def sync_schedule_rules(data):
    '''Receives node IP, sends API call to write node current schedule rules to
    node disk, downloads modified config from node and writes to django database.
    Called when user clicks yes on notification after modifying schedule rule.
    '''
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

        # Overwrite config in database
        node.config.config = json.loads(config_file)
        node.config.save()

        return standard_response('Done syncing schedule rules')

    return error_response(message='Failed to save rules', status=500)


@requires_post
def send_command(data):
    '''Sends API call specified in body to ESP32 node specified in body.
    Bridges frontend HTTP requests to non-standard ESP32 asyncio API (faster).
    '''

    # Get target node IP and API endpoint
    ip = data["target"]
    cmd = data["command"]
    del data["target"], data["command"]

    # Add endpoint (must be first) followed by remaining args
    args = [cmd]
    for param in data.values():
        # Remove extra whitespace from strings
        if isinstance(param, str):
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


def parse_command(ip, args):
    '''Takes target IP + args list (first item must be endpoint name).
    Find endpoint matching first arg, call handler function with remaining args.
    '''
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


def parse_command_wrapper(node, args):
    '''Takes node instead of IP, returns JSON-printable dict with response.
    Used by bulk command endpoints (reboot_all, reset_all_rules, etc).
    '''
    response = parse_command(node.ip, args)
    return {
        'node': node.friendly_name,
        'response': response
    }


def run_macro(request, name):
    '''Takes name of Macro model entry, runs all actions in parallel.'''
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
    '''Adds the specified macro action to the specified Macro model entry.'''
    try:
        macro = Macro.objects.get(name=data['name'])
    except Macro.DoesNotExist:
        macro = Macro.objects.create(name=data['name'])

    try:
        macro.add_action(data['action'])
    except (SyntaxError, KeyError):
        # Delete empty macro if failed to add first action
        if not json.loads(macro.actions):
            macro.delete()
        return error_response('Invalid action', status=400)

    print(f"Added action: {data['action']}")

    return standard_response(message='Done')


def delete_macro(request, name):
    '''Deletes the specified Macro model entry.'''
    try:
        macro = Macro.objects.get(name=name)
    except Macro.DoesNotExist:
        return error_response(message=f'Macro {name} does not exist', status=404)

    macro.delete()

    return standard_response(message='Done')


def delete_macro_action(request, name, index):
    '''Deletes specified macro action index in specified Macro model entry.'''
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
    '''Takes macro name entered by user when record button clicked.
    Returns 200 if macro name is unique, 409 if duplicate.
    '''
    try:
        Macro.objects.get(name=name)
        return error_response(message=f'Name {name} already in use', status=409)
    except Macro.DoesNotExist:
        return standard_response(message=f'Name {name} available')


def get_macro_actions(request, name):
    '''Takes name of Macro model entry, returns actions as JSON.'''
    try:
        macro = Macro.objects.get(name=name)
        return standard_response(message=json.loads(macro.actions))
    except Macro.DoesNotExist:
        return error_response(message=f'Macro {name} does not exist', status=404)


# Returns cookie to skip record macro instructions popup
def skip_instructions(request):
    '''Returns cookie that prevents record macro instructions from opening.'''
    response = HttpResponse()
    response.set_cookie('skip_instructions', 'true')
    return response


@requires_post
def edit_ir_macro(data):
    '''Takes JSON with IR Blaster macro name and actions.
    Sends API call to ESP32 to delete existing macro with same name (if any),
    then sends API calls to add each action and write the macro to ESP32 disk.
    '''
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
    '''Takes JSON with IR Blaster macro name and actions.
    Sends API calls to ESP32 to add each action and write the macro to disk.
    '''
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
