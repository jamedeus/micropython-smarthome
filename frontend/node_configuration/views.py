import json
from functools import wraps
from concurrent.futures import ThreadPoolExecutor
from django.shortcuts import render
from django.http import JsonResponse
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from .models import Node, Config, WifiCredentials, ScheduleKeyword, GpsCoordinates
from Webrepl import Webrepl
from provision_tools import get_modules, provision
from .get_api_target_menu_options import get_api_target_menu_options
from api_endpoints import add_schedule_keyword, remove_schedule_keyword, save_schedule_keywords, set_gps_coords
from validation_constants import config_templates
from validate_config import validate_full_config
from helper_functions import (
    is_device_or_sensor,
    is_device,
    is_sensor,
    valid_ip,
    get_schedule_keywords_dict,
    get_config_filename,
    get_device_and_sensor_metadata
)

# Env var constants
REPO_DIR = settings.REPO_DIR
NODE_PASSWD = settings.NODE_PASSWD


# Decorator used throw error if request is not POST
# Passes parsed JSON body to wrapped function as first arg
def requires_post(func):
    @wraps(func)
    def wrapper(request, **kwargs):
        if request.method == "POST":
            data = json.loads(request.body.decode("utf-8"))
        else:
            return JsonResponse({'Error': 'Must post data'}, safe=False, status=405)
        return func(data, **kwargs)
    return wrapper


@requires_post
def upload(data, reupload=False):
    if not valid_ip(data["ip"]):
        return JsonResponse({'Error': f'Invalid IP {data["ip"]}'}, safe=False, status=400)

    try:
        config = Config.objects.get(filename=data["config"])
    except Config.DoesNotExist:
        return JsonResponse("ERROR: Config file doesn't exist - did you delete it manually?", safe=False, status=404)

    # Get dependencies, upload
    modules = get_modules(config.config, REPO_DIR)
    response = provision(data["ip"], NODE_PASSWD, config.config, modules)

    # If uploaded for the first time, update models
    if response['status'] == 200 and not reupload:
        new = Node.objects.create(
            friendly_name=config.config["metadata"]["id"],
            ip=data["ip"],
            floor=config.config["metadata"]["floor"]
        )

        config.node = new
        config.save()

    return JsonResponse(response['message'], safe=False, status=response['status'])


def reupload_all(request):
    print("Reuploading all configs...")
    nodes = Node.objects.all()

    # Track success/failure of each upload
    report = {'success': [], 'failed': {}}

    for node in nodes:
        modules = get_modules(node.config.config, REPO_DIR)

        print(f"\nReuploading {node.friendly_name}...")
        response = provision(node.ip, NODE_PASSWD, node.config.config, modules)

        # Add result to report
        if response['status'] == 200:
            report['success'].append(node.friendly_name)
        elif response['status'] == 404:
            report['failed'][node.friendly_name] = 'Offline'
        elif response['status'] == 408:
            report['failed'][node.friendly_name] = 'Connection timed out'
        elif response['status'] == 409:
            report['failed'][node.friendly_name] = 'Filesystem error'

    print('\nreupload_all results:')
    print(json.dumps(report, indent=4))

    return JsonResponse(report, safe=False, status=200)


@requires_post
def delete_config(data):
    try:
        # Get model entry
        target = Config.objects.get(filename=data)
    except Config.DoesNotExist:
        return JsonResponse(f"Failed to delete {data}, does not exist", safe=False, status=404)

    try:
        target.delete()
        return JsonResponse(f"Deleted {data}", safe=False, status=200)
    except PermissionError:
        return JsonResponse(
            "Failed to delete, permission denied. This will break other features, check your filesystem permissions.",
            safe=False,
            status=500
        )


@requires_post
def delete_node(data):
    try:
        # Get model entry
        node = Node.objects.get(friendly_name=data)
    except Node.DoesNotExist:
        return JsonResponse(f"Failed to delete {data}, does not exist", safe=False, status=404)

    try:
        # Delete from database and disk
        node.delete()
        return JsonResponse(f"Deleted {data}", safe=False, status=200)
    except PermissionError:
        return JsonResponse(
            "Failed to delete, permission denied. This will break other features, check your filesystem permissions.",
            safe=False,
            status=500
        )


@requires_post
def change_node_ip(data):
    if not valid_ip(data["new_ip"]):
        return JsonResponse({'Error': f'Invalid IP {data["new_ip"]}'}, safe=False, status=400)

    try:
        # Get model entry, delete from disk + database
        node = Node.objects.get(friendly_name=data['friendly_name'])
    except Node.DoesNotExist:
        return JsonResponse("Unable to change IP, node does not exist", safe=False, status=404)

    if node.ip == data["new_ip"]:
        return JsonResponse({'Error': 'New IP must be different than old'}, safe=False, status=400)

    # Get dependencies, upload to new IP
    modules = get_modules(node.config.config, REPO_DIR)
    response = provision(data["new_ip"], NODE_PASSWD, node.config.config, modules)

    if response['status'] == 200:
        # Update model
        node.ip = data["new_ip"]
        node.save()

        return JsonResponse("Successfully uploaded to new IP", safe=False, status=200)
    else:
        return JsonResponse(response['message'], safe=False, status=response['status'])


def config_overview(request):
    context = {
        "not_uploaded": [],
        "uploaded": [],
        "schedule_keywords": get_schedule_keywords_dict()
    }

    # Reverse proxy connection: Add forwarded_for IP to context
    if 'HTTP_X_FORWARDED_FOR' in request.META:
        context['client_ip'] = request.META.get('HTTP_X_FORWARDED_FOR')
    # Direct connection: Add client IP to context
    else:
        context['client_ip'] = request.META.get('REMOTE_ADDR')

    # Don't show sunrise or sunset (prevent editing time, overwrites on nodes)
    del context["schedule_keywords"]["sunrise"]
    del context["schedule_keywords"]["sunset"]

    not_uploaded = Config.objects.filter(node=None)

    for i in not_uploaded:
        context["not_uploaded"].append(str(i))

    uploaded = Node.objects.all()
    for i in uploaded:
        context["uploaded"].append(i)

    return render(request, 'node_configuration/overview.html', context)


# Returns context object with relevant parameters from device and sensor metadata
# Used to populate configuration divs with appropriate inputs based on type
def get_metadata_context():
    # Get object containing all device/sensor metadata
    metadata = get_device_and_sensor_metadata()
    context = {'devices': {}, 'sensors': {}}

    for i in metadata['devices']:
        config_name = i['config_name']
        template = i['config_template']
        # Extract params which require user input
        params = [i for i in template.keys() if i not in ['_type', 'nickname', 'default_rule', 'schedule', 'targets']]
        context['devices'][config_name] = {}
        context['devices'][config_name]['type'] = config_name
        context['devices'][config_name]['name'] = i['class_name']
        context['devices'][config_name]['prompt'] = i['rule_prompt']
        context['devices'][config_name]['params'] = params

        # Add rule limits if present
        if 'rule_limits' in i.keys():
            context['devices'][config_name]['rule_limits'] = i['rule_limits']

    for i in metadata['sensors']:
        config_name = i['config_name']
        template = i['config_template']
        # Extract params which require user input
        params = [i for i in template.keys() if i not in ['_type', 'nickname', 'default_rule', 'schedule', 'targets']]
        context['sensors'][config_name] = {}
        context['sensors'][config_name]['type'] = config_name
        context['sensors'][config_name]['name'] = i['class_name']
        context['sensors'][config_name]['prompt'] = i['rule_prompt']
        context['sensors'][config_name]['params'] = params

        # Add rule limits if present
        if 'rule_limits' in i.keys():
            context['sensors'][config_name]['rule_limits'] = i['rule_limits']

    return context


def new_config(request):
    # Create context with config skeleton
    context = {
        "config": {
            "TITLE": "Create New Config",
            'metadata': {
                'id': '',
                'floor': '',
                'location': '',
                'schedule_keywords': get_schedule_keywords_dict()
            },
            'wifi': {
                'ssid': '',
                'password': ''
            },
        },
        "api_target_options": get_api_target_menu_options(),
        "metadata": get_metadata_context(),
        "edit_existing": False
    }

    # Add default wifi credentials if configured
    if len(WifiCredentials.objects.all()) > 0:
        default = WifiCredentials.objects.all()[0]
        context["config"]["wifi"]["ssid"] = default.ssid
        context["config"]["wifi"]["password"] = default.password

    # Add device and sensor config templates
    context['templates'] = config_templates

    return render(request, 'node_configuration/edit-config.html', context)


def edit_config(request, name):
    try:
        target = Node.objects.get(friendly_name=name)
    except Node.DoesNotExist:
        return JsonResponse({'Error': f'{name} node not found'}, safe=False, status=404)

    config = target.config.config

    config["NAME"] = target.friendly_name
    config["TITLE"] = f"Editing {target.friendly_name}"
    config["IP"] = target.ip
    config["FILENAME"] = target.config.filename

    sensors = {}
    devices = {}
    instances = {}
    delete = []

    metadata = get_metadata_context()

    for i in config:
        if is_sensor(i):
            # Add to instances
            instances[i] = {}
            instances[i]["type"] = config[i]["_type"]
            instances[i]["nickname"] = config[i]["nickname"]
            instances[i]["schedule"] = config[i]["schedule"]

            # Add to sensors, change _type to type (django template limitation)
            sensors[i] = config[i]
            sensors[i]["type"] = config[i]["_type"]
            sensors[i]["metadata"] = metadata["sensors"][config[i]["_type"]]
            del sensors[i]["_type"]

            # Add to delete list
            delete.append(i)

        elif is_device(i):
            # Add to instances
            instances[i] = {}
            instances[i]["type"] = config[i]["_type"]
            instances[i]["nickname"] = config[i]["nickname"]
            instances[i]["schedule"] = config[i]["schedule"]

            # Add to delete list
            delete.append(i)

            # Add to devices, change _type to type (django template limitation)
            devices[i] = config[i]
            devices[i]["type"] = config[i]["_type"]
            devices[i]["metadata"] = metadata["devices"][config[i]["_type"]]
            del devices[i]["_type"]

            # Correct ApiTarget rule syntax
            if devices[i]["type"] == "api-target":
                devices[i]["default_rule"] = json.dumps(devices[i]["default_rule"])

                for rule in instances[i]["schedule"]:
                    instances[i]["schedule"][rule] = json.dumps(instances[i]["schedule"][rule])

    for i in delete:
        del config[i]

    # Add completed dicts to context with keys sorted alphabetically
    # Template relies on forloop.counter to determine ID, will not match config if not alphabetical
    config["sensors"] = {sensor: sensors[sensor] for sensor in sorted(sensors)}
    config["devices"] = {device: devices[device] for device in sorted(devices)}
    config["instances"] = {instance: instances[instance] for instance in sorted(instances)}

    api_target_options = get_api_target_menu_options(target.friendly_name)

    context = {
        "config": config,
        "api_target_options": api_target_options,
        "metadata": metadata,
        "edit_existing": True
    }

    # Add device and sensor config templates
    context['templates'] = config_templates

    print(json.dumps(context, indent=4))

    return render(request, 'node_configuration/edit-config.html', context)


# Return True if filename or friendly_name would conflict with an existing config or node
def is_duplicate(filename, friendly_name):
    # Check if filename will conflict with existing configs
    try:
        Config.objects.get(filename=filename)
        return True
    except Config.DoesNotExist:
        pass

    # Check if friendly name is a duplicate, must be unique for frontend
    try:
        Node.objects.get(friendly_name=friendly_name)
        return True
    except Node.DoesNotExist:
        return False


# Used to warn when duplicate name entered in config generator
@requires_post
def check_duplicate(data):
    friendly_name = data['name']
    filename = get_config_filename(friendly_name)

    if is_duplicate(filename, friendly_name):
        return JsonResponse("ERROR: Config already exists with identical name.", safe=False, status=409)
    else:
        return JsonResponse("Name OK.", safe=False, status=200)


@requires_post
def generate_config_file(data, edit_existing=False):
    print("Input:")
    print(json.dumps(data, indent=4))

    # Delete title, only used for template
    del data['TITLE']

    # Cast floor to int (required by validator)
    # TODO does this really matter? Why was the validator added?
    data['metadata']['floor'] = int(data['metadata']['floor'])

    # Get filename (all lowercase, replace spaces with hyphens)
    filename = get_config_filename(data["metadata"]["id"])

    print(f"\nFilename: {filename}\n")

    # Confirm config exists when editing existing
    if edit_existing:
        try:
            model_entry = Config.objects.get(filename=filename)
        except Config.DoesNotExist:
            return JsonResponse({'Error': 'Config not found'}, safe=False, status=404)

    # Prevent overwriting existing config, unless editing existing
    if not edit_existing and is_duplicate(filename, data["metadata"]["id"]):
        return JsonResponse("ERROR: Config already exists with identical name.", safe=False, status=409)

    # If default location set, add coordinates to config
    if len(GpsCoordinates.objects.all()) > 0:
        location = GpsCoordinates.objects.all()[0]
        data["metadata"]["gps"] = {"lat": str(location.lat), "lon": str(location.lon)}

    # If config contains ApiTarget, convert string rules to dict
    for i in [i for i in data.keys() if is_device(i)]:
        if data[i]['_type'] == 'api-target':
            data[i]['default_rule'] = json.loads(data[i]['default_rule'])
            for rule in data[i]['schedule']:
                data[i]['schedule'][rule] = json.loads(data[i]['schedule'][rule])

    print("Output:")
    print(json.dumps(data, indent=4))

    # Validate completed config, return error if invalid
    valid = validate_full_config(data)
    if valid is not True:
        print(f"\nERROR: {valid}\n")
        return JsonResponse({'Error': valid}, safe=False, status=400)

    # If creating new config, add to models + write to disk
    if not edit_existing:
        new = Config.objects.create(config=data, filename=filename)
        new.write_to_disk()

    # If modifying old config, update JSON object and write to disk
    else:
        model_entry.config = data
        model_entry.save()

    return JsonResponse("Config created.", safe=False, status=200)


@requires_post
def set_default_credentials(data):
    # If default already set, overwrite
    if len(WifiCredentials.objects.all()) > 0:
        for i in WifiCredentials.objects.all():
            i.delete()

    new = WifiCredentials(ssid=data["ssid"], password=data["password"])
    new.save()

    return JsonResponse("Default credentials set", safe=False, status=200)


@requires_post
def set_default_location(data):
    # If default already set, overwrite
    if len(GpsCoordinates.objects.all()) > 0:
        for i in GpsCoordinates.objects.all():
            i.delete()

    # Instantiate model
    GpsCoordinates.objects.create(display=data["name"], lat=data["lat"], lon=data["lon"])

    # Add coordinates to all existing nodes in parallel
    commands = [(node.ip, {'latitude': data["lat"], 'longitude': data["lon"]}) for node in Node.objects.all()]
    with ThreadPoolExecutor(max_workers=20) as executor:
        executor.map(set_gps_coords, *zip(*commands))

    # Add coordinates to all existing configs
    for config in Config.objects.all():
        config.config['metadata']['gps'] = {'lat': data['lat'], 'lon': data['lon']}
        config.save()

    return JsonResponse("Location set", safe=False, status=200)


# Downloads config file from an existing node and saves to database + disk
@requires_post
def restore_config(data):
    if not valid_ip(data["ip"]):
        return JsonResponse({'Error': f'Invalid IP {data["ip"]}'}, safe=False, status=400)

    # Open conection, detect if node connected to network
    node = Webrepl(data["ip"], NODE_PASSWD)
    if not node.open_connection():
        return JsonResponse(
            "Error: Unable to connect to node, please make sure it is connected to wifi and try again.",
            safe=False,
            status=404
        )

    # Download config file from node, parse json
    config = node.get_file_mem("config.json")
    config = json.loads(config)

    # Get filename (all lowercase, replace spaces with hyphens)
    filename = get_config_filename(config["metadata"]["id"])

    # Prevent overwriting existing config
    if is_duplicate(filename, config['metadata']['id']):
        return JsonResponse("ERROR: Config already exists with identical name.", safe=False, status=409)

    # Overwrite schedule keywords with keywords from database
    config['metadata']['schedule_keywords'] = get_schedule_keywords_dict()

    # Confirm received config is valid
    valid = validate_full_config(config)
    if valid is not True:
        return JsonResponse("ERROR: Config format invalid, possibly outdated version.", safe=False, status=500)

    # Create Config model entry
    config = Config(config=config, filename=filename)

    # Create Node model entry
    node = Node.objects.create(
        friendly_name=config.config["metadata"]["id"],
        ip=data["ip"],
        floor=config.config["metadata"]["floor"]
    )

    # Add reverse relation
    config.node = node
    config.save()

    return JsonResponse("Config restored", safe=False, status=200)


@requires_post
def add_schedule_keyword_config(data):
    # Create keyword in database
    try:
        ScheduleKeyword.objects.create(keyword=data["keyword"], timestamp=data["timestamp"])
    except ValidationError as ex:
        return JsonResponse(str(ex), safe=False, status=400)

    # Add keyword to all existing nodes in parallel
    commands = [(node.ip, [data["keyword"], data["timestamp"]]) for node in Node.objects.all()]
    with ThreadPoolExecutor(max_workers=20) as executor:
        executor.map(add_schedule_keyword, *zip(*commands))

    # Save keywords on all nodes
    save_all_schedule_keywords()

    # Add new keyword to all configs in database and on disk
    all_keywords = get_schedule_keywords_dict()
    for node in Node.objects.all():
        node.config.config['metadata']['schedule_keywords'] = all_keywords
        node.config.save()

    return JsonResponse("Keyword created", safe=False, status=200)


@requires_post
def edit_schedule_keyword_config(data):
    try:
        target = ScheduleKeyword.objects.get(keyword=data["keyword_old"])
    except ScheduleKeyword.DoesNotExist:
        return JsonResponse({'Error': 'Keyword not found'}, safe=False, status=404)

    target.keyword = data["keyword_new"]
    target.timestamp = data["timestamp_new"]

    try:
        target.save()
    except ValidationError as ex:
        return JsonResponse(str(ex), safe=False, status=400)

    # If timestamp changed: Call add to overwrite existing keyword
    if data["keyword_old"] == data["keyword_new"]:
        # Update keyword on all existing nodes in parallel
        commands = [(node.ip, [data["keyword_new"], data["timestamp_new"]]) for node in Node.objects.all()]
        with ThreadPoolExecutor(max_workers=20) as executor:
            executor.map(add_schedule_keyword, *zip(*commands))

    # If keyword changed: Remove existing keyword, add new keyword
    else:
        # Remove keyword from all existing nodes in parallel
        commands = [(node.ip, [data["keyword_old"]]) for node in Node.objects.all()]
        with ThreadPoolExecutor(max_workers=20) as executor:
            executor.map(remove_schedule_keyword, *zip(*commands))

        # Add keyword to all existing nodes in parallel
        commands = [(node.ip, [data["keyword_new"], data["timestamp_new"]]) for node in Node.objects.all()]
        with ThreadPoolExecutor(max_workers=20) as executor:
            executor.map(add_schedule_keyword, *zip(*commands))

    # Save keywords on all nodes
    save_all_schedule_keywords()

    # Update keywords for all configs in database and on disk
    all_keywords = get_schedule_keywords_dict()
    for node in Node.objects.all():
        node.config.config['metadata']['schedule_keywords'] = all_keywords
        node.config.save()

    return JsonResponse("Keyword updated", safe=False, status=200)


@requires_post
def delete_schedule_keyword_config(data):
    try:
        target = ScheduleKeyword.objects.get(keyword=data["keyword"])
    except ScheduleKeyword.DoesNotExist:
        return JsonResponse({'Error': 'Keyword not found'}, safe=False, status=404)

    try:
        target.delete()
    except IntegrityError as ex:
        return JsonResponse(str(ex), safe=False, status=400)

    # Remove keyword from all existing nodes in parallel
    commands = [(node.ip, [data["keyword"]]) for node in Node.objects.all()]
    with ThreadPoolExecutor(max_workers=20) as executor:
        executor.map(remove_schedule_keyword, *zip(*commands))

    # Save keywords on all nodes
    save_all_schedule_keywords()

    # Remove keyword from all configs in database and from disk
    all_keywords = get_schedule_keywords_dict()
    for node in Node.objects.all():
        node.config.config['metadata']['schedule_keywords'] = all_keywords
        node.config.save()

    return JsonResponse("Keyword deleted", safe=False, status=200)


# Call save_schedule_keywords for all nodes in parallel
def save_all_schedule_keywords():
    commands = [(node.ip, "") for node in Node.objects.all()]
    with ThreadPoolExecutor(max_workers=20) as executor:
        executor.map(save_schedule_keywords, *zip(*commands))
