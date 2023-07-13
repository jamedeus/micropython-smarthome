import json
import os
from concurrent.futures import ThreadPoolExecutor
from django.shortcuts import render
from django.http import JsonResponse
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from .models import Node, Config, WifiCredentials, ScheduleKeyword, GpsCoordinates
from Webrepl import Webrepl
from provision_tools import get_modules, provision
from instance_validators import validate_rules
from .get_api_target_menu_options import get_api_target_menu_options
from api_endpoints import add_schedule_keyword, remove_schedule_keyword, save_schedule_keywords
from validation_constants import valid_device_pins, valid_sensor_pins, config_templates, valid_config_keys
from helper_functions import (
    is_device_or_sensor,
    is_device,
    is_sensor,
    get_config_param_list,
    valid_ip,
    get_schedule_keywords_dict
)

# Env var constants
REPO_DIR = settings.REPO_DIR
CONFIG_DIR = settings.CONFIG_DIR
NODE_PASSWD = settings.NODE_PASSWD

# Parse tuple of device and sensor types from templates, used in validation
valid_device_types = tuple([config_templates['device'][i]['_type'] for i in config_templates['device'].keys()])
valid_sensor_types = tuple([config_templates['sensor'][i]['_type'] for i in config_templates['sensor'].keys()])


def upload(request, reupload=False):
    if request.method == "POST":
        data = json.loads(request.body.decode("utf-8"))
    else:
        return JsonResponse({'Error': 'Must post data'}, safe=False, status=405)

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


def delete_config(request):
    if request.method == "POST":
        data = json.loads(request.body.decode("utf-8"))
    else:
        return JsonResponse({'Error': 'Must post data'}, safe=False, status=405)

    try:
        # Get model entry
        target = Config.objects.get(filename=data)
    except Config.DoesNotExist:
        return JsonResponse(f"Failed to delete {data}, does not exist", safe=False, status=404)

    try:
        # Delete from disk + database
        os.remove(f'{CONFIG_DIR}/{target.filename}')
        target.delete()
        return JsonResponse(f"Deleted {data}", safe=False, status=200)

    except FileNotFoundError:
        # Missing from disk: Delete from database and return normal response
        target.delete()
        return JsonResponse(f"Deleted {data}", safe=False, status=200)

    except PermissionError:
        return JsonResponse(
            "Failed to delete, permission denied. This will break other features, check your filesystem permissions.",
            safe=False,
            status=500
        )


def delete_node(request):
    if request.method == "POST":
        data = json.loads(request.body.decode("utf-8"))
    else:
        return JsonResponse({'Error': 'Must post data'}, safe=False, status=405)

    try:
        # Get model entry
        node = Node.objects.get(friendly_name=data)
    except Node.DoesNotExist:
        return JsonResponse(f"Failed to delete {data}, does not exist", safe=False, status=404)

    try:
        # Delete from disk
        os.remove(f'{CONFIG_DIR}/{node.config.filename}')
    except PermissionError:
        return JsonResponse(
            "Failed to delete, permission denied. This will break other features, check your filesystem permissions.",
            safe=False,
            status=500
        )
    except FileNotFoundError:
        pass

    # Delete from database
    node.delete()
    return JsonResponse(f"Deleted {data}", safe=False, status=200)


def change_node_ip(request):
    if request.method == "POST":
        data = json.loads(request.body.decode("utf-8"))
    else:
        return JsonResponse({'Error': 'Must post data'}, safe=False, status=405)

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
        "schedule_keywords": get_schedule_keywords_dict(),
        "client_ip": request.META.get('REMOTE_ADDR')
    }

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


def new_config(request):
    context = {
        "config": {"TITLE": "Create New Config"},
        "api_target_options": get_api_target_menu_options()
    }

    # Add default wifi credentials if configured
    if len(WifiCredentials.objects.all()) > 0:
        default = WifiCredentials.objects.all()[0]
        context["config"]["wifi"] = {}
        context["config"]["wifi"]["ssid"] = default.ssid
        context["config"]["wifi"]["password"] = default.password

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

    context = {"config": config, "api_target_options": api_target_options}

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
def check_duplicate(request):
    if request.method == "POST":
        data = json.loads(request.body.decode("utf-8"))
    else:
        return JsonResponse({'Error': 'Must post data'}, safe=False, status=405)

    friendly_name = data['name']
    filename = friendly_name.lower().replace(" ", "-") + ".json"

    if is_duplicate(filename, friendly_name):
        return JsonResponse("ERROR: Config already exists with identical name.", safe=False, status=409)
    else:
        return JsonResponse("Name OK.", safe=False, status=200)


# Accepts completed config, returns True if all device and sensor types are valid, error string if invalid
def validate_instance_types(config):
    # Get device and sensor IDs
    devices = [key for key in config.keys() if is_device(key)]
    sensors = [key for key in config.keys() if is_sensor(key)]

    # Get device and sensor types
    device_types = [config[device]['_type'] for device in devices]
    sensor_types = [config[sensor]['_type'] for sensor in sensors]

    # Check for invalid device/sensor types
    for dtype in device_types:
        if dtype not in valid_device_types:
            return f'Invalid device type {dtype} used'

    for stype in sensor_types:
        if stype not in valid_sensor_types:
            return f'Invalid sensor type {stype} used'

    return True


# Accepts completed config, returns True if all device and sensor pins are valid, error string if invalid
def validate_instance_pins(config):
    # Get device and sensor pins
    try:
        device_pins = [int(val['pin']) for key, val in config.items() if is_device(key) and 'pin' in val]
        sensor_pins = [int(val['pin']) for key, val in config.items() if is_sensor(key) and 'pin' in val]
    except ValueError:
        return 'Invalid pin (non-integer)'

    # Check for invalid pins (reserved, input-only, etc)
    for pin in device_pins:
        if str(pin) not in valid_device_pins:
            return f'Invalid device pin {pin} used'

    for pin in sensor_pins:
        if str(pin) not in valid_sensor_pins:
            return f'Invalid sensor pin {pin} used'

    return True


# Accepts complete config + template with correct keys
# Recursively checks that each template key also exists in config
def validate_config_keys(config, valid_config_keys):
    for key in valid_config_keys:
        if key not in config:
            return f"Missing required top-level {key} key"
        elif isinstance(valid_config_keys[key], dict):
            if validate_config_keys(config[key], valid_config_keys[key]) is not True:
                return f"Missing required key in {key} section"
    return True


# Accepts completed config, return True if valid, error string if invalid
def validate_full_config(config):
    # Confirm config has all required keys (see valid_config_keys)
    valid = validate_config_keys(config, valid_config_keys)
    if valid is not True:
        return valid

    # Floor must be integer
    try:
        int(config['metadata']['floor'])
    except ValueError:
        return 'Invalid floor, must be integer'

    # Get list of all nicknames, check for duplicates
    nicknames = get_config_param_list(config, 'nickname')
    if len(nicknames) != len(set(nicknames)):
        return 'Contains duplicate nicknames'

    # Get list of all pins, check for duplicates
    pins = get_config_param_list(config, 'pin')
    if len(pins) != len(set(pins)):
        return 'Contains duplicate pins'

    # Check if all device and sensor types are valid
    valid = validate_instance_types(config)
    if valid is not True:
        return valid

    # Check if all device and sensor pins are valid
    valid = validate_instance_pins(config)
    if valid is not True:
        return valid

    # Check if all IP addresses are valid
    ips = [value['ip'] for key, value in config.items() if 'ip' in value]
    for ip in ips:
        if not valid_ip(ip):
            return f'Invalid IP {ip}'

    # Validate rules for all devices and sensors
    for instance in [key for key in config.keys() if is_device_or_sensor(key)]:
        valid = validate_rules(config[instance])
        if valid is not True:
            print(f"\nERROR: {valid}\n")
            return valid

    return True


def generate_config_file(request, edit_existing=False):
    if request.method == "POST":
        data = json.loads(request.body.decode("utf-8"))
    else:
        return JsonResponse({'Error': 'Must post data'}, safe=False, status=405)

    print("Input:")
    print(json.dumps(data, indent=4))

    # Get filename (all lowercase, replace spaces with hyphens)
    filename = data["friendlyName"].lower().replace(" ", "-") + ".json"

    print(f"\nFilename: {filename}\n")

    # Confirm config exists when editing existing
    if edit_existing:
        try:
            model_entry = Config.objects.get(filename=filename)
        except Config.DoesNotExist:
            return JsonResponse({'Error': 'Config not found'}, safe=False, status=404)

    # Prevent overwriting existing config, unless editing existing
    if not edit_existing and is_duplicate(filename, data["friendlyName"]):
        return JsonResponse("ERROR: Config already exists with identical name.", safe=False, status=409)

    # Populate metadata and credentials directly from JSON
    config = {
        "metadata": {
            "id": data["friendlyName"],
            "location": data["location"],
            "floor": data["floor"],
            "schedule_keywords": get_schedule_keywords_dict()
        },
        "wifi": {
            "ssid": data["ssid"],
            "password": data["password"]
        }
    }

    # If default location set, add coordinates to config
    if len(GpsCoordinates.objects.all()) > 0:
        location = GpsCoordinates.objects.all()[0]
        config["metadata"]["gps"] = {"lat": str(location.lat), "lon": str(location.lon)}

    # Add all devices and sensors to config
    for i in data:
        # IrBlaster handled different than devices (not triggered by sensors, does not have _type)
        if is_device(i) and data[i]["_type"] == "ir-blaster":
            config["ir_blaster"] = data[i]
            del config["ir_blaster"]["_type"]

        # Convert ApiTarget rules to correct format
        elif is_device(i) and data[i]["_type"] == "api-target":
            config[i] = data[i]
            config[i]["default_rule"] = json.loads(config[i]["default_rule"])
            for rule in config[i]["schedule"]:
                config[i]["schedule"][rule] = json.loads(config[i]["schedule"][rule])

        # No changes needed for all other devices and sensors
        elif is_device_or_sensor(i):
            config[i] = data[i]

    print("Output:")
    print(json.dumps(config, indent=4))

    # Validate completed config, return error if invalid
    valid = validate_full_config(config)
    if valid is not True:
        print(f"\nERROR: {valid}\n")
        return JsonResponse({'Error': valid}, safe=False, status=400)

    # If creating new config, add to models + write to disk
    if not edit_existing:
        new = Config.objects.create(config=config, filename=filename)
        new.write_to_disk()

    # If modifying old config, update JSON object and write to disk
    else:
        model_entry.config = config
        model_entry.save()
        model_entry.write_to_disk()

    return JsonResponse("Config created.", safe=False, status=200)


def set_default_credentials(request):
    if request.method == "POST":
        data = json.loads(request.body.decode("utf-8"))
    else:
        return JsonResponse({'Error': 'Must post data'}, safe=False, status=405)

    # If default already set, overwrite
    if len(WifiCredentials.objects.all()) > 0:
        for i in WifiCredentials.objects.all():
            i.delete()

    new = WifiCredentials(ssid=data["ssid"], password=data["password"])
    new.save()

    return JsonResponse("Default credentials set", safe=False, status=200)


def set_default_location(request):
    if request.method == "POST":
        data = json.loads(request.body.decode("utf-8"))
    else:
        return JsonResponse({'Error': 'Must post data'}, safe=False, status=405)

    # If default already set, overwrite
    if len(GpsCoordinates.objects.all()) > 0:
        for i in GpsCoordinates.objects.all():
            i.delete()

    GpsCoordinates.objects.create(display=data["name"], lat=data["lat"], lon=data["lon"])
    return JsonResponse("Location set", safe=False, status=200)


# Downloads config file from an existing node and saves to database + disk
def restore_config(request):
    if request.method == "POST":
        data = json.loads(request.body.decode("utf-8"))
    else:
        return JsonResponse({'Error': 'Must post data'}, safe=False, status=405)

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
    filename = config["metadata"]["id"].lower().replace(" ", "-") + ".json"

    # Prevent overwriting existing config
    if is_duplicate(filename, config['metadata']['id']):
        return JsonResponse("ERROR: Config already exists with identical name.", safe=False, status=409)

    # Overwrite schedule keywords with keywords from database
    config['metadata']['schedule_keywords'] = get_schedule_keywords_dict()

    # Confirm received config is valid
    valid = validate_full_config(config)
    if valid is not True:
        return JsonResponse("ERROR: Config format invalid, possibly outdated version.", safe=False, status=500)

    # Write file to disk
    with open(CONFIG_DIR + filename, 'w') as file:
        json.dump(config, file)

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


def add_schedule_keyword_config(request):
    if request.method == "POST":
        data = json.loads(request.body.decode("utf-8"))
    else:
        return JsonResponse({'Error': 'Must post data'}, safe=False, status=405)

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
        node.config.write_to_disk()

    return JsonResponse("Keyword created", safe=False, status=200)


def edit_schedule_keyword_config(request):
    if request.method == "POST":
        data = json.loads(request.body.decode("utf-8"))
    else:
        return JsonResponse({'Error': 'Must post data'}, safe=False, status=405)

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
        node.config.write_to_disk()

    return JsonResponse("Keyword updated", safe=False, status=200)


def delete_schedule_keyword_config(request):
    if request.method == "POST":
        data = json.loads(request.body.decode("utf-8"))
    else:
        return JsonResponse({'Error': 'Must post data'}, safe=False, status=405)

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
        node.config.write_to_disk()

    return JsonResponse("Keyword deleted", safe=False, status=200)


# Call save_schedule_keywords for all nodes in parallel
def save_all_schedule_keywords():
    commands = [(node.ip, "") for node in Node.objects.all()]
    with ThreadPoolExecutor(max_workers=20) as executor:
        executor.map(save_schedule_keywords, *zip(*commands))
