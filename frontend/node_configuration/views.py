from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponse, Http404, JsonResponse, FileResponse
from django.template import loader
import json
import os

from .models import Node, Config, WifiCredentials

from .webrepl_cli import *

REPO_DIR = os.environ.get('REPO_DIR')
CONFIG_DIR = os.environ.get('CONFIG_DIR')
NODE_PASSWD = os.environ.get('NODE_PASSWD')

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

        elif conf[i]["type"] == "wled":
            modules.append("devices/Wled.py")
            modules.append("devices/Device.py")

    # Remove duplicates
    modules = set(modules)

    return modules, libs



def upload(request, reupload=False):
    if request.method == "POST":
        data = json.loads(request.body.decode("utf-8"))
    else:
        raise Http404("ERROR: Must post data")

    try:
        config = Config.objects.get(filename = data["config"])
    except Config.DoesNotExist:
        return JsonResponse("ERROR: Config file doesn't exist - did you delete it manually?", safe=False, status=200)

    if not data["config"] == "setup.json":
        modules, libs = get_modules(config.config)
    else:
        modules = []
        libs = []

    # Upload
    response = provision(data["config"], data["ip"], modules, libs)

    # If uploaded for the first time, update models
    if response.status_code == 200 and not reupload:
        new = Node(friendly_name = config.config["metadata"]["id"], ip = data["ip"], floor = config.config["metadata"]["floor"])
        new.save()

        config.node = new
        config.save()

    return response



def provision(config, ip, modules, libs):
    def open_connection():
        try:
            s = socket.socket()
            s.settimeout(10)
            ai = socket.getaddrinfo(ip, 8266)
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
        put_file(ws, CONFIG_DIR + config, "config.json")

        # Upload Config module
        put_file(ws, REPO_DIR + "Config.py", "Config.py")

        # Upload Group module
        put_file(ws, REPO_DIR + "Group.py", "Group.py")

        # Upload SoftwareTimer module
        put_file(ws, REPO_DIR + "SoftwareTimer.py", "SoftwareTimer.py")

        # Upload API module
        put_file(ws, REPO_DIR + "Api.py", "Api.py")

        if not config == "setup.json":
            # Upload main code last (triggers automatic reboot)
            put_file(ws, REPO_DIR + "boot.py", "boot.py")
        else:
            put_file(ws, REPO_DIR + "setup.py", "boot.py")

        close_connection(s)

    except ConnectionResetError:
        return JsonResponse("Connection error, please hold down the reset button on target node and try again after about 30 seconds.", safe=False, status=408)
    except OSError:
        return JsonResponse("Unable to connect - please ensure target node is plugged in and wait for the blue light to turn off, then try again.", safe=False, status=408)
    except AssertionError:
        print(f"can't upload {src_file}")
        if src_file.split("/")[-2] == "lib":
            print("lib")
            return JsonResponse("ERROR: Unable to upload libraries, /lib/ does not exist. This is normal for new nodes - would you like to upload setup to fix?", safe=False, status=409)

    return JsonResponse("Upload complete.", safe=False, status=200)



def reupload_all(request):
    print("Reuploading all configs...")
    nodes = Node.objects.all()

    for node in nodes:
        modules, libs = get_modules(node.config.config)

        print(f"\nReuploading {node.friendly_name}...")
        provision(node.config.filename, node.ip, modules, libs)

    return JsonResponse("Finished reuploading", safe=False, status=200)



def delete_config(request):
    if request.method == "POST":
        data = json.loads(request.body.decode("utf-8"))
    else:
        raise Http404("ERROR: Must post data")

    target = Config.objects.get(filename = data)
    target.delete()
    os.system(f'rm {CONFIG_DIR}/{target.filename}')

    return JsonResponse("Deleted {}".format(data), safe=False, status=200)



def delete_node(request):
    if request.method == "POST":
        data = json.loads(request.body.decode("utf-8"))
    else:
        raise Http404("ERROR: Must post data")

    # Get model entry
    node = Node.objects.get(friendly_name = data)

    # Delete from disk, delete from models
    os.system(f'rm {CONFIG_DIR}/{node.config.filename}')
    node.delete()

    return JsonResponse("Deleted {}".format(data), safe=False, status=200)



def node_configuration(request):
    context = {
        "not_uploaded" : [],
        "uploaded" : []
    }

    not_uploaded = Config.objects.filter(node = None)

    for i in not_uploaded:
        context["not_uploaded"].append(str(i))

    uploaded = Node.objects.all()
    for i in uploaded:
        context["uploaded"].append(i)

    template = loader.get_template('node_configuration/overview.html')

    return HttpResponse(template.render({'context': context}, request))



def configure(request):
    template = loader.get_template('node_configuration/edit-config.html')

    context = {"config": {"TITLE": "Create New Config"}, "api_target_options": get_api_target_menu_options()}

    # Add default wifi credentials if configured
    if len(WifiCredentials.objects.all()) > 0:
        default = WifiCredentials.objects.all()[0]
        context["config"]["wifi"] = {}
        context["config"]["wifi"]["ssid"] = default.ssid
        context["config"]["wifi"]["password"] = default.password

    return HttpResponse(template.render({'context': context}, request))



def edit_config(request, name):
    target = Node.objects.get(friendly_name = name)

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

    #print(json.dumps(config, indent=4))

    template = loader.get_template('node_configuration/edit-config.html')

    api_target_options = get_api_target_menu_options(target.friendly_name)

    context = {"config": config, "api_target_options": api_target_options}

    print(json.dumps(context, indent=4))

    return HttpResponse(template.render({'context': context}, request))



def generateConfigFile(request, edit_existing=False):
    if request.method == "POST":
        data = json.loads(request.body.decode("utf-8"))
    else:
        raise Http404("ERROR: Must post data")

    print("Input:")
    print(json.dumps(data, indent=4))

    try:
        # Check if file with identical parameters exists in database
        duplicate = Config.objects.get(filename = data["friendlyName"])

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
            config[i]["default_rule"] = json.loads(config[i]["default_rule"])

            for rule in config[i]["schedule"]:
                config[i]["schedule"][rule] = json.loads(config[i]["schedule"][rule])

    # If IrBlaster configured, move to seperate section with different syntax
    if irblaster:
        config["ir_blaster"] = config[irblaster]
        del config[irblaster]
        del config["ir_blaster"]["type"]
        del config["ir_blaster"]["schedule"]

    print("\nOutput:")
    print(json.dumps(config, indent=4))

    # Get filename (all lowercase, replace spaces with hyphens)
    filename = config["metadata"]["id"].lower().replace(" ", "-") + ".json"

    print(f"\n\n{filename}\n\n")

    # If creating new config, add to models + write to disk
    if not edit_existing:
        new = Config(config = config, filename = filename)
        new.save()
        new.write_to_disk()

    # If modifying old config, update JSON object and write to disk
    else:
        old = Config.objects.get(filename=filename)
        old.config = config
        old.save()
        old.write_to_disk()

    return JsonResponse("Config created.", safe=False, status=200)



# Return dict with all configured nodes, their devices and sensors, and API commands which target each device/sensor type
# If friendly name of existing node passed as arg, name and IP are replaced with "self-target" and "127.0.0.1" respectively
# Used to populate cascading dropdown menu in frontend
def get_api_target_menu_options(editing_node=False):
    dropdownObject = {}
    dropdownObject['addresses'] = {}

    # Add self-target option
    dropdownObject['self-target'] = {}
    dropdownObject['addresses']['self-target'] = '127.0.0.1'

    for node in Node.objects.all():
        entries = {}

        config = node.config.config

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

        if editing_node and node.friendly_name == editing_node:
            dropdownObject["self-target"] = entries
        else:
            dropdownObject[node.friendly_name] = entries
            dropdownObject['addresses'][node.friendly_name] = node.ip

    return dropdownObject



def set_default_credentials(request):
    if request.method == "POST":
        data = json.loads(request.body.decode("utf-8"))
    else:
        raise Http404("ERROR: Must post data")

    # If default already set, overwrite
    if len(WifiCredentials.objects.all()) > 0:
        for i in WifiCredentials.objects.all():
            i.delete()

    new = WifiCredentials(ssid = data["ssid"], password = data["password"])
    new.save()

    return JsonResponse("Default credentials set", safe=False, status=200)
