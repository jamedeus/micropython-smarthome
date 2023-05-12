import json
import os
import re
from concurrent.futures import ThreadPoolExecutor
from django.shortcuts import render
from django.http import JsonResponse
from django.conf import settings
from django.core.exceptions import ValidationError
from .models import Node, Config, WifiCredentials, ScheduleKeyword
from .Webrepl import Webrepl
from .validators import validate_rules
from .get_api_target_menu_options import get_api_target_menu_options
from api.views import add_schedule_keyword, remove_schedule_keyword

REPO_DIR = settings.REPO_DIR
CONFIG_DIR = settings.CONFIG_DIR
NODE_PASSWD = settings.NODE_PASSWD

# Config validation constants
valid_device_pins = (4, 13, 16, 17, 18, 19, 21, 22, 23, 25, 26, 27, 32, 33)
valid_sensor_pins = (4, 5, 13, 14, 15, 16, 17, 18, 19, 21, 22, 23, 25, 26, 27, 32, 33, 34, 35, 36, 39)
valid_device_types = ('dimmer', 'bulb', 'relay', 'dumb-relay', 'desktop', 'pwm', 'mosfet', 'api-target', 'wled')
valid_sensor_types = ('pir', 'desktop', 'si7021', 'dummy', 'switch')

# Dependency relative paths for all device and sensor types, used by get_modules
dependencies = {
    'devices': {
        'dimmer': ["devices/Tplink.py", "devices/Device.py"],
        'bulb': ["devices/Tplink.py", "devices/Device.py"],
        'relay': ["devices/Relay.py", "devices/Device.py"],
        'dumb-relay': ["devices/DumbRelay.py", "devices/Device.py"],
        'desktop': ["devices/Desktop_target.py", "devices/Device.py"],
        'pwm': ["devices/LedStrip.py", "devices/Device.py"],
        'mosfet': ["devices/Mosfet.py", "devices/Device.py"],
        'api-target': ["devices/ApiTarget.py", "devices/Device.py"],
        'wled': ["devices/Wled.py", "devices/Device.py"]
    },
    'sensors': {
        'pir': ["sensors/MotionSensor.py", "sensors/Sensor.py"],
        'si7021': ["sensors/Thermostat.py", "sensors/Sensor.py"],
        'dummy': ["sensors/Dummy.py", "sensors/Sensor.py"],
        'switch': ["sensors/Switch.py", "sensors/Sensor.py"],
        'desktop': ["sensors/Desktop_trigger.py", "sensors/Sensor.py"],
    }
}


# Returns True if param matches IPv4 regex, otherwise False
def valid_ip(ip):
    return bool(re.match("^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$", ip))


# Returns all schedule keywords in dict format used by node config files and overview template
def get_schedule_keywords_dict():
    return {keyword.keyword: keyword.timestamp for keyword in ScheduleKeyword.objects.all()}


# Takes full config file, returns all dependencies in 2 lists:
# - modules: classes for all configured devices and sensors
# - libs: libraries required by configured devices and sensors
def get_modules(config):
    modules = []
    libs = ['lib/logging.py']

    # Get lists of device and sensor types
    device_types = [config[device]['type'] for device in config.keys() if device.startswith('device')]
    sensor_types = [config[sensor]['type'] for sensor in config.keys() if sensor.startswith('sensor')]

    # Get dependencies for all device and sensor types
    for dtype in device_types:
        modules.extend(dependencies['devices'][dtype])
    for stype in sensor_types:
        modules.extend(dependencies['sensors'][stype])

    # Add libs if thermostat or ir_blaster configured
    if 'si7021' in sensor_types:
        libs.append("lib/si7021.py")
    if 'ir_blaster' in config.keys():
        modules.extend(["devices/IrBlaster.py", "ir-remote/samsung-codes.json", "ir-remote/whynter-codes.json"])
        libs.extend(["lib/ir_tx/__init__.py", "lib/ir_tx/nec.py"])

    # Remove duplicates
    modules = set(modules)

    # Convert to dict containing pairs of local:remote filesystem paths
    # Local path is uploaded to remote path on target ESP32
    modules = {os.path.join(REPO_DIR, i): i.split("/")[1] for i in modules}
    libs = {os.path.join(REPO_DIR, i): i for i in libs}

    return modules, libs


def setup(request):
    if request.method == "POST":
        data = json.loads(request.body.decode("utf-8"))
        print(json.dumps(data, indent=4))
    else:
        return JsonResponse({'Error': 'Must post data'}, safe=False, status=405)

    if not valid_ip(data["ip"]):
        return JsonResponse({'Error': f'Invalid IP {data["ip"]}'}, safe=False, status=400)

    # Upload
    return provision("setup.json", data["ip"], {}, {})


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
    modules, libs = get_modules(config.config)
    response = provision(data["config"], data["ip"], modules, libs)

    # If uploaded for the first time, update models
    if response.status_code == 200 and not reupload:
        new = Node.objects.create(
            friendly_name=config.config["metadata"]["id"],
            ip=data["ip"],
            floor=config.config["metadata"]["floor"]
        )

        config.node = new
        config.save()

    return response


# Takes path to config file, target ip, and modules + libs dicts from get_modules()
# Uploads config, modules, libs, and core to target IP
def provision(config, ip, modules, libs):
    # Open conection, detect if node connected to network
    node = Webrepl(ip, NODE_PASSWD)
    if not node.open_connection():
        return JsonResponse("Error: Unable to connect to node, please make sure it is connected to wifi and try again.", safe=False, status=404)

    try:
        # Upload all device/sensor modules
        [node.put_file(local, remote) for local, remote in modules.items()]

        # Upload all libraries
        try:
            [node.put_file(local, remote) for local, remote in libs.items()]
        except AssertionError:
            return JsonResponse("ERROR: Unable to upload libraries, /lib/ does not exist. This is normal for new nodes - would you like to upload setup to fix?", safe=False, status=409)

        # Upload core dependencies
        [node.put_file(os.path.join(REPO_DIR, i), i) for i in ["Config.py", "Group.py", "SoftwareTimer.py", "Api.py"]]

        # Upload config file
        node.put_file(os.path.join(CONFIG_DIR, config), "config.json")

        # Upload boot file last (triggers automatic reboot)
        if not config == "setup.json":
            node.put_file(os.path.join(REPO_DIR, "boot.py"), "boot.py")
        else:
            # First-time setup, creates /lib/ and subdirs
            node.put_file(os.path.join(REPO_DIR, "setup.py"), "boot.py")

        node.close_connection()

    except TimeoutError:
        return JsonResponse("Connection timed out - please press target node reset button, wait 30 seconds, and try again.", safe=False, status=408)
    except AssertionError:
        return JsonResponse("ERROR: Upload failed due to filesystem problem, please re-flash node.", safe=False, status=409)

    return JsonResponse("Upload complete.", safe=False, status=200)


def reupload_all(request):
    print("Reuploading all configs...")
    nodes = Node.objects.all()

    # Track success/failure of each upload
    report = {'success': [], 'failed': {}}

    for node in nodes:
        modules, libs = get_modules(node.config.config)

        print(f"\nReuploading {node.friendly_name}...")
        response = provision(node.config.filename, node.ip, modules, libs)

        # Add result to report
        if response.status_code == 200:
            report['success'].append(node.friendly_name)
        elif response.status_code == 404:
            report['failed'][node.friendly_name] = 'Offline'
        elif response.status_code == 408:
            report['failed'][node.friendly_name] = 'Connection timed out'
        elif response.status_code == 409:
            report['failed'][node.friendly_name] = 'Requires setup'

    print('\nreupload_all results:')
    print(json.dumps(report, indent=4))

    return JsonResponse(report, safe=False, status=200)


def delete_config(request):
    if request.method == "POST":
        data = json.loads(request.body.decode("utf-8"))
    else:
        return JsonResponse({'Error': 'Must post data'}, safe=False, status=405)

    try:
        # Get model entry, delete from disk + database
        target = Config.objects.get(filename=data)
        os.remove(f'{CONFIG_DIR}/{target.filename}')
        target.delete()
        return JsonResponse(f"Deleted {data}", safe=False, status=200)

    except Config.DoesNotExist:
        return JsonResponse(f"Failed to delete {data}, does not exist", safe=False, status=404)
    except PermissionError:
        return JsonResponse("Failed to delete, permission denied. This will break other features, check your filesystem permissions.", safe=False, status=500)


def delete_node(request):
    if request.method == "POST":
        data = json.loads(request.body.decode("utf-8"))
    else:
        return JsonResponse({'Error': 'Must post data'}, safe=False, status=405)

    try:
        # Get model entry, delete from disk + database
        node = Node.objects.get(friendly_name=data)
        os.remove(f'{CONFIG_DIR}/{node.config.filename}')
        node.delete()
        return JsonResponse(f"Deleted {data}", safe=False, status=200)

    except Node.DoesNotExist:
        return JsonResponse(f"Failed to delete {data}, does not exist", safe=False, status=404)
    except PermissionError:
        return JsonResponse("Failed to delete, permission denied. This will break other features, check your filesystem permissions.", safe=False, status=500)


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
    modules, libs = get_modules(node.config.config)
    response = provision(node.config.filename, data["new_ip"], modules, libs)

    if response.status_code == 200:
        # Update model
        node.ip = data["new_ip"]
        node.save()

        return JsonResponse("Successfully uploaded to new IP", safe=False, status=200)
    else:
        return response


def config_overview(request):
    context = {
        "not_uploaded": [],
        "uploaded": [],
        "schedule_keywords": get_schedule_keywords_dict()
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
    target = Node.objects.get(friendly_name=name)

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
        if i.startswith("sensor"):
            sensors[i] = config[i]
            delete.append(i)
            instances[i] = {}
            instances[i]["type"] = config[i]["type"]
            instances[i]["nickname"] = config[i]["nickname"]
            instances[i]["schedule"] = config[i]["schedule"]
        elif i.startswith("device"):
            devices[i] = config[i]
            delete.append(i)
            instances[i] = {}
            instances[i]["type"] = config[i]["type"]
            instances[i]["nickname"] = config[i]["nickname"]
            instances[i]["schedule"] = config[i]["schedule"]

            if config[i]["type"] == "api-target":
                devices[i]["default_rule"] = json.dumps(devices[i]["default_rule"])

                for rule in instances[i]["schedule"]:
                    instances[i]["schedule"][rule] = json.dumps(instances[i]["schedule"][rule])

    for i in delete:
        del config[i]

    config["sensors"] = sensors
    config["devices"] = devices
    config["instances"] = instances

    api_target_options = get_api_target_menu_options(target.friendly_name)

    context = {"config": config, "api_target_options": api_target_options}

    print(json.dumps(context, indent=4))

    return render(request, 'node_configuration/edit-config.html', context)


# Return True if filename or friendly_name would conflict with an existing config or node
def is_duplicate(filename, friendly_name):
    # Check if filename will conflict with existing configs
    try:
        duplicate = Config.objects.get(filename=filename)
        return True
    except Config.DoesNotExist:
        pass

    # Check if friendly name is a duplicate, must be unique for frontend
    try:
        duplicate = Node.objects.get(friendly_name=friendly_name)
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


# Accepts completed config, return True if valid, error string if invalid
def validateConfig(config):
    # Floor must be integer
    try:
        int(config['metadata']['floor'])
    except ValueError:
        return 'Invalid floor, must be integer'

    # No duplicate nicknames
    nicknames = [value['nickname'] for key, value in config.items() if 'nickname' in value]
    if len(nicknames) != len(set(nicknames)):
        return 'Contains duplicate nicknames'

    # No duplicate pins
    pins = [value['pin'] for key, value in config.items() if 'pin' in value]
    if len(pins) != len(set(pins)):
        return 'Contains duplicate pins'

    # Get device and sensor IDs
    devices = [key for key in config.keys() if key.startswith('device')]
    sensors = [key for key in config.keys() if key.startswith('sensor')]

    # Get device and sensor types
    device_types = [config[device]['type'] for device in devices]
    sensor_types = [config[sensor]['type'] for sensor in sensors]

    # Get device and sensor pins
    try:
        device_pins = [int(value['pin']) for key, value in config.items() if key.startswith('device') and 'pin' in value]
        sensor_pins = [int(value['pin']) for key, value in config.items() if key.startswith('sensor') and 'pin' in value]
    except ValueError:
        return 'Invalid pin (non-integer)'

    # Check for invalid device/sensor types
    for dtype in device_types:
        if dtype not in valid_device_types:
            return f'Invalid device type {dtype} used'

    for stype in sensor_types:
        if stype not in valid_sensor_types:
            return f'Invalid sensor type {stype} used'

    # Check for invalid pins (reserved, input-only, etc)
    for pin in device_pins:
        if pin not in valid_device_pins:
            return f'Invalid device pin {pin} used'

    for pin in sensor_pins:
        if pin not in valid_sensor_pins:
            return f'Invalid sensor pin {pin} used'

    # Validate IP addresses
    ips = [value['ip'] for key, value in config.items() if 'ip' in value]
    for ip in ips:
        if not valid_ip(ip):
            return f'Invalid IP {ip}'

    # Validate Thermostat tolerance
    for sensor in sensors:
        if config[sensor]['type'] == 'si7021':
            tolerance = config[sensor]['tolerance']
            try:
                if not 0.1 <= float(tolerance) <= 10.0:
                    return 'Thermostat tolerance out of range (0.1 - 10.0)'
            except ValueError:
                return f'Invalid thermostat tolerance {config[sensor]["tolerance"]}'

    # Validate PWM limits
    for device in devices:
        if config[device]['type'] == 'pwm':
            minimum = config[device]['min']
            maximum = config[device]['max']

            try:
                if int(minimum) > int(maximum):
                    return 'PWM min cannot be greater than max'
                elif int(minimum) < 0 or int(maximum) < 0:
                    return 'PWM limits cannot be less than 0'
                elif int(minimum) > 1023 or int(maximum) > 1023:
                    return 'PWM limits cannot be greater than 1023'

            except ValueError:
                return 'Invalid PWM limits, both must be int between 0 and 1023'

    # Validate rules for all devices and sensors
    instances = devices + sensors
    for i in instances:
        valid = validate_rules(config[i])
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

    # Prevent overwriting existing config, unless editing existing
    if not edit_existing:
        if is_duplicate(filename, data["friendlyName"]):
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

    # Add device and sensor sections from JSON
    for i in data["devices"]:
        config[i] = data["devices"][i]

    for i in data["sensors"]:
        config[i] = data["sensors"][i]

    # Remove parameters only used by frontend
    for i in config:
        if i.startswith("device") or i.startswith("sensor"):
            del config[i]["id"]
            del config[i]["new"]
            del config[i]["modified"]

    irblaster = False

    for i in config:
        if i.startswith("device") and config[i]["type"] == "ir-blaster":
            irblaster = i

        # Convert ApiTarget rules to correct format
        elif i.startswith("device") and config[i]["type"] == "api-target":
            config[i]["default_rule"] = json.loads(config[i]["default_rule"])

            for rule in config[i]["schedule"]:
                config[i]["schedule"][rule] = json.loads(config[i]["schedule"][rule])

    # If IrBlaster configured, move to seperate section with different syntax
    if irblaster:
        config["ir_blaster"] = config[irblaster]
        del config[irblaster]
        del config["ir_blaster"]["type"]
        del config["ir_blaster"]["schedule"]

    print("Output:")
    print(json.dumps(config, indent=4))

    # Validate completed config, return error if invalid
    valid = validateConfig(config)
    if valid is not True:
        print(f"\nERROR: {valid}\n")
        return JsonResponse({'Error': valid}, safe=False, status=400)

    # If creating new config, add to models + write to disk
    if not edit_existing:
        new = Config(config=config, filename=filename)
        new.save()
        new.write_to_disk()

    # If modifying old config, update JSON object and write to disk
    else:
        old = Config.objects.get(filename=filename)
        old.config = config
        old.save()
        old.write_to_disk()

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
        return JsonResponse("Error: Unable to connect to node, please make sure it is connected to wifi and try again.", safe=False, status=404)

    # Download config file from node, parse json
    config = node.get_file_mem("config.json")
    config = json.loads(config)

    # Get filename (all lowercase, replace spaces with hyphens)
    filename = config["metadata"]["id"].lower().replace(" ", "-") + ".json"

    # Prevent overwriting existing config
    if is_duplicate(filename, config['metadata']['id']):
        return JsonResponse("ERROR: Config already exists with identical name.", safe=False, status=409)

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

    return JsonResponse("Keyword created", safe=False, status=200)


def edit_schedule_keyword_config(request):
    if request.method == "POST":
        data = json.loads(request.body.decode("utf-8"))
    else:
        return JsonResponse({'Error': 'Must post data'}, safe=False, status=405)

    target = ScheduleKeyword.objects.get(keyword=data["keyword_old"])

    target.keyword = data["keyword_new"]
    target.timestamp = data["timestamp_new"]

    try:
        target.save()
    except:
        return JsonResponse("Failed to update keyword", safe=False, status=400)

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

    return JsonResponse("Keyword updated", safe=False, status=200)


def delete_schedule_keyword_config(request):
    if request.method == "POST":
        data = json.loads(request.body.decode("utf-8"))
    else:
        return JsonResponse({'Error': 'Must post data'}, safe=False, status=405)

    target = ScheduleKeyword.objects.get(keyword=data["keyword"])

    try:
        target.delete()
    except:
        return JsonResponse("Failed to delete keyword", safe=False, status=500)

    # Remove keyword from all existing nodes in parallel
    commands = [(node.ip, [data["keyword"]]) for node in Node.objects.all()]
    with ThreadPoolExecutor(max_workers=20) as executor:
        executor.map(remove_schedule_keyword, *zip(*commands))

    return JsonResponse("Keyword deleted", safe=False, status=200)
