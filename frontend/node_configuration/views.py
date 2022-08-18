from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponse, Http404, JsonResponse, FileResponse
from django.template import loader
import json
import os

from .models import Node, Config

from .webrepl_cli import *

REPO_DIR = "/home/jamedeus/git/micropython-smarthome/"
CONFIG_DIR = "/home/jamedeus/git/micropython-smarthome/config/"
NODE_PASSWD = "password"

def get_modules(conf):
    modules = []
    libs = []
    libs.append('lib/logging.py')

    for i in conf:
        if i == "ir_blaster":
            modules.append("devices/IrBlaster.py")
            modules.append("ir-remote/samsung-codes.json")
            modules.append("ir-remote/whynter-codes.json")
            libs.append("lib/ir_tx/__init__.py")
            libs.append("lib/ir_tx/nec.py")
            continue

        if not i.startswith("device") and not i.startswith("sensor"): continue

        if conf[i]["type"] == "dimmer" or conf[i]["type"] == "bulb":
            modules.append("devices/Tplink.py")
            modules.append("devices/Device.py")

        elif conf[i]["type"] == "relay":
            modules.append("devices/Relay.py")
            modules.append("devices/Device.py")

        elif conf[i]["type"] == "dumb-relay":
            modules.append("devices/DumbRelay.py")
            modules.append("devices/Device.py")

        elif conf[i]["type"] == "desktop":
            if i.startswith("device"):
                modules.append("devices/Desktop_target.py")
                modules.append("devices/Device.py")
            elif i.startswith("sensor"):
                modules.append("sensors/Desktop_trigger.py")
                modules.append("sensors/Sensor.py")

        elif conf[i]["type"] == "pwm":
            modules.append("devices/LedStrip.py")
            modules.append("devices/Device.py")

        elif conf[i]["type"] == "mosfet":
            modules.append("devices/Mosfet.py")
            modules.append("devices/Device.py")

        elif conf[i]["type"] == "api-target":
            modules.append("devices/ApiTarget.py")
            modules.append("devices/Device.py")

        elif conf[i]["type"] == "pir":
            modules.append("sensors/MotionSensor.py")
            modules.append("sensors/Sensor.py")

        elif conf[i]["type"] == "si7021":
            modules.append("sensors/Thermostat.py")
            modules.append("sensors/Sensor.py")
            libs.append("lib/si7021.py")

        elif conf[i]["type"] == "dummy":
            modules.append("sensors/Dummy.py")
            modules.append("sensors/Sensor.py")

        elif conf[i]["type"] == "switch":
            modules.append("sensors/Switch.py")
            modules.append("sensors/Sensor.py")

    # Remove duplicates
    modules = set(modules)

    return modules, libs



def upload(request, reupload=False):
    if request.method == "POST":
        data = json.loads(request.body.decode("utf-8"))
    else:
        raise Http404("ERROR: Must post data")

    try:
        with open(CONFIG_DIR + data["config"], 'r') as file:
            config = json.load(file)
    except FileNotFoundError:
        return JsonResponse("ERROR: Config file doesn't exist - did you delete it manually?", safe=False, status=200)

    if not data["config"] == "setup.json":
        modules, libs = get_modules(config)
    else:
        modules = []
        libs = []

    def open_connection():
        try:
            s = socket.socket()
            s.settimeout(10)
            ai = socket.getaddrinfo(data["ip"], 8266)
            addr = ai[0][4]
            s.connect(addr)
            websocket_helper.client_handshake(s)
            ws = websocket(s)
            login(ws, NODE_PASSWD)
            ws.ioctl(9, 2)

            return ws, s

        except OSError:
            close_connection(s)
            return False, False

    def close_connection(s):
        s.close()

    # Open conection, detect if node connected to network
    ws, s = open_connection()
    if not ws:
        return JsonResponse("Error: Unable to connect to node, please make sure it is connected to wifi and try again.", safe=False, status=404)

    try:
        # Upload all device/sensor modules
        for i in modules:
            src_file = REPO_DIR + i
            dst_file = i.rsplit("/", 1)[-1] # Remove path from filename

            put_file(ws, src_file, dst_file)

        # Upload all libraries
        for i in libs:
            src_file = REPO_DIR + i
            dst_file = i

            put_file(ws, src_file, dst_file)

        # Upload config file
        put_file(ws, CONFIG_DIR + data["config"], "config.json")

        # Upload Config module
        put_file(ws, REPO_DIR + "Config.py", "Config.py")

        # Upload Group module
        put_file(ws, REPO_DIR + "Group.py", "Group.py")

        # Upload SoftwareTimer module
        put_file(ws, REPO_DIR + "SoftwareTimer.py", "SoftwareTimer.py")

        # Upload API module
        put_file(ws, REPO_DIR + "Api.py", "Api.py")

        if not data["config"] == "setup.json":
            # Upload main code last (triggers automatic reboot)
            put_file(ws, REPO_DIR + "boot.py", "boot.py")
        else:
            put_file(ws, REPO_DIR + "setup.py", "boot.py")

        close_connection(s)

    except ConnectionResetError:
        return JsonResponse("Connection error, please hold down the reset button on target node and try again after about 30 seconds.", safe=False, status=200)
    except OSError:
        return JsonResponse("Unable to connect - please ensure target node is plugged in and wait for the blue light to turn off, then try again.", safe=False, status=200)
    except AssertionError:
        print(f"can't upload {src_file}")
        if src_file.split("/")[-2] == "lib":
            print("lib")
            return JsonResponse("ERROR: Unable to upload libraries, /lib/ does not exist. This is normal for new nodes - would you like to upload setup to fix?", safe=False, status=409)

    # If uploaded for the first time, update models
    if not reupload:
        target = Config.objects.get(config_file = CONFIG_DIR + data["config"])
        target.uploaded = True
        target.save()

        new = Node(friendly_name = config["metadata"]["id"], ip = data["ip"], config_file = CONFIG_DIR + data["config"])
        new.save()

    return JsonResponse("Upload complete.", safe=False, status=200)



def delete_config(request):
    if request.method == "POST":
        data = json.loads(request.body.decode("utf-8"))
    else:
        raise Http404("ERROR: Must post data")

    target = Config.objects.get(config_file__endswith = data)
    target.delete()
    os.system(f'rm {target.config_file}')

    return JsonResponse("Deleted {}".format(data), safe=False, status=200)



def delete_node(request):
    if request.method == "POST":
        data = json.loads(request.body.decode("utf-8"))
    else:
        raise Http404("ERROR: Must post data")

    # Get both model entries
    node = Node.objects.get(friendly_name = data)
    config = Config.objects.get(config_file = node.config_file)

    # Delete from disk, delete from models
    os.system(f'rm {node.config_file}')
    config.delete()
    node.delete()

    return JsonResponse("Deleted {}".format(data), safe=False, status=200)



def node_configuration(request):
    context = {
        "not_uploaded" : [],
        "uploaded" : []
    }

    not_uploaded = Config.objects.filter(uploaded = False)

    for i in not_uploaded:
        context["not_uploaded"].append(str(i).split("/")[-1])

    uploaded = Node.objects.all()
    for i in uploaded:
        context["uploaded"].append(i)

    template = loader.get_template('node_configuration/overview.html')

    return HttpResponse(template.render({'context': context}, request))



def configure(request):
    template = loader.get_template('node_configuration/edit-config.html')

    context = {"config": {"TITLE": "Create New Config"}, "api_target_options": get_api_target_menu_options()}

    return HttpResponse(template.render({'context': context}, request))



def edit_config(request, name):
    target = Node.objects.get(friendly_name = name)

    with open(target.config_file, 'r') as file:
        config = json.load(file)

    config["NAME"] = target.friendly_name
    config["TITLE"] = f"Editing {target.friendly_name}"
    config["IP"] = target.ip
    config["FILENAME"] = target.config_file.split("/")[-1]

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
            instances[i]["schedule"] = config[i]["schedule"]
        elif i.startswith("device"):
            devices[i] = config[i]
            delete.append(i)
            instances[i] = {}
            instances[i]["type"] = config[i]["type"]
            instances[i]["schedule"] = config[i]["schedule"]

            if config[i]["type"] == "api-target":
                devices[i]["default_rule"] = reverse_convert_api_target_rule(devices[i]["default_rule"])

                for rule in instances[i]["schedule"]:
                    instances[i]["schedule"][rule] = reverse_convert_api_target_rule(instances[i]["schedule"][rule])

    for i in delete:
        del config[i]

    config["sensors"] = sensors
    config["devices"] = devices
    config["instances"] = instances

    print(json.dumps(config, indent=4))

    template = loader.get_template('node_configuration/edit-config.html')

    api_target_options = get_api_target_menu_options()

    context = {"config": config, "api_target_options": api_target_options}

    return HttpResponse(template.render({'context': context}, request))



def generateConfigFile(request, edit_existing=False):
    if request.method == "POST":
        data = json.loads(request.body.decode("utf-8"))
    else:
        raise Http404("ERROR: Must post data")

    try:
        # Check if file with identical parameters exists in database
        duplicate = Config.objects.get(config_file = CONFIG_DIR + data["friendlyName"] + ".json")

        # Ignore duplicate error if editing an existing config
        if not edit_existing:
            return JsonResponse("ERROR: Config already exists with identical name.", safe=False, status=409)

    except Config.DoesNotExist:
        pass

    # Populate metadata and credentials directly from JSON
    config = {
        "metadata": {
            "id" : data["friendlyName"],
            "location" : data["location"],
            "floor" : data["floor"]
        },
        "wifi": {
            "ssid" : data["ssid"],
            "password" : data["password"]
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
            config[i]["ip"] = config[i]["ip"].split("-")[0]

            config[i]["default_rule"] = convert_api_target_rule(config[i]["default_rule"])

            for rule in config[i]["schedule"]:
                config[i]["schedule"][rule] = convert_api_target_rule(config[i]["schedule"][rule])

    # If IrBlaster configured, move to seperate section with different syntax
    if irblaster:
        config["ir_blaster"] = config[i]
        del config[irblaster]
        del config["ir_blaster"]["type"]
        del config["ir_blaster"]["schedule"]

    print("Input:")
    print(json.dumps(data, indent=4))

    print("\nOutput:")
    print(json.dumps(config, indent=4))

    # Get filename (all lowercase, replace spaces with hyphens)
    filename = config["metadata"]["id"].lower().replace(" ", "-")

    with open(CONFIG_DIR + filename + ".json", 'w') as file:
        json.dump(config, file)

    # If creating a new config, add to models
    if not edit_existing:
        new = Config(config_file = CONFIG_DIR + filename + ".json", uploaded = False)
        new.save()

    return JsonResponse("Config created.", safe=False, status=200)



# Return dict with all configured nodes, their devices and sensors, and API commands which target each device/sensor type
# Used to populate cascading dropdown menu in frontent
def get_api_target_menu_options():
    dropdownObject = {}

    for node in Node.objects.all():
        entries = {}

        with open(node.config_file, 'r') as file:
            config = json.load(file)

        for i in config:
            if i.startswith("device"):
                instance_string = f'{i}-{config[i]["nickname"]} ({config[i]["type"]})'

                entry = ['enable', 'disable', 'enable_in', 'disable_in', 'set_rule', 'reset_rule', 'reboot', 'turn_on', 'turn_off']

            elif i.startswith("sensor"):
                instance_string = f'{i}-{config[i]["nickname"]} ({config[i]["type"]})'

                entry = ['enable', 'disable', 'enable_in', 'disable_in', 'set_rule', 'reset_rule', 'reboot']

                if not (config[i]["type"] == "si7021" or config[i]["type"] == "switch"):
                    entry.append("trigger_sensor")

            elif i == "ir_blaster":
                instance_string = "ir_blaster-Ir Blaster"
                entry = {'tv': ['power', 'vol_up', 'vol_down', 'mute', 'up', 'down', 'left', 'right', 'enter', 'settings', 'exit', 'source'], 'ac': [ 'start', 'stop', 'off' ]}

            else:
                continue

            entries[instance_string] = entry

        dropdownObject[f"{node.ip}-{node.friendly_name}"] = entries

    return dropdownObject



# Convert stringified JSON received from frontend to ApiTarget rule format dict
def convert_api_target_rule(rule):
    rule = json.loads(rule)

    output = {"on": [], "off": []}

    if rule["instance-on"] == "ir_blaster":
        output["on"].append("ir_key")
        output["on"].append(rule["command-on"])
        output["on"].append(rule["sub-command-on"])

    else:
        output["on"].append(rule["command-on"])
        output["on"].append(rule["instance-on"])

        if "command-arg-on" in rule.keys():
            output["on"].append(rule["command-arg-on"])

    if rule["instance-off"] == "ir_blaster":
        output["off"].append("ir_key")
        output["off"].append(rule["command-off"])
        output["off"].append(rule["sub-command-off"])

    else:
        output["off"].append(rule["command-off"])
        output["off"].append(rule["instance-off"])

        if "command-arg-off" in rule.keys():
            output["off"].append(rule["command-arg-off"])

    return output



def reverse_convert_api_target_rule(rule):
    result = {}

    if rule["on"][0] == "ir_key":
        result["instance-on"] = "ir_blaster"
        result["command-on"] = rule["on"][1]
        result["sub-command-on"] = rule["on"][2]
    else:
        result["instance-on"] = rule["on"][1]
        result["command-on"] = rule["on"][0]

        if result["command-on"] in ("enable_in", "disable_in", "set_rule"):
            result["command-arg-on"] = rule["on"][2]

    if rule["off"][0] == "ir_key":
        result["instance-off"] = "ir_blaster"
        result["command-off"] = rule["off"][1]
        result["sub-command-off"] = rule["off"][2]
    else:
        result["instance-off"] = rule["off"][1]
        result["command-off"] = rule["off"][0]

        if result["command-off"] in ("enable_in", "disable_in", "set_rule"):
            result["command-arg-off"] = rule["off"][2]

    return json.dumps(result)
