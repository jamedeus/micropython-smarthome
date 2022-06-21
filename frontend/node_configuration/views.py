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



def upload(request):
    if request.method == "POST":
        data = json.loads(request.body.decode("utf-8"))
    else:
        raise Http404("ERROR: Must post data")

    try:
        with open(CONFIG_DIR + data["config"], 'r') as file:
            config = json.load(file)
    except FileNotFoundError:
        return JsonResponse("ERROR: Config file doesn't exist - did you delete it manually?", safe=False, status=200)

    modules, libs = get_modules(config)

    try:
        s = socket.socket()
        ai = socket.getaddrinfo(data["ip"], 8266)
        addr = ai[0][4]
        s.connect(addr)
        websocket_helper.client_handshake(s)
        ws = websocket(s)
        login(ws, NODE_PASSWD)
        ws.ioctl(9, 2)

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

        # Upload SoftwareTimer module
        put_file(ws, REPO_DIR + "SoftwareTimer.py", "SoftwareTimer.py")

        # Upload API module
        put_file(ws, REPO_DIR + "Api.py", "Api.py")

        # Upload main code last (triggers automatic reboot)
        put_file(ws, REPO_DIR + "boot.py", "boot.py")

    except ConnectionResetError:
        return JsonResponse("Connection error, please hold down the reset button on target node and try again after about 30 seconds.", safe=False, status=200)
    except OSError:
        return JsonResponse("Unable to connect - please ensure target node is plugged in and wait for the blue light to turn off, then try again.", safe=False, status=200)

    # Update database
    target = Config.objects.get(config_file = CONFIG_DIR + data["config"])
    target.uploaded = True
    target.save()

    new = Node(friendly_name = config["metadata"]["id"], ip = data["ip"], config_file = CONFIG_DIR + data["config"])
    new.save()

    return JsonResponse("Upload complete.", safe=False, status=200)



def node_configuration_index(request):
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

    template = loader.get_template('node_configuration/index.html')

    return HttpResponse(template.render({'context': context}, request))



def configure(request):
    template = loader.get_template('node_configuration/configure.html')

    return HttpResponse(template.render({}, request))



def configure_page2(request):
    if request.method == "POST":
        data = json.loads(request.body.decode("utf-8"))
    else:
        raise Http404("ERROR: Must post data")

    config = {
        "devices" : {},
        "sensors" : {}
    }

    for i in data.keys():
        if i.startswith("deviceType") or i.startswith("sensorType"):
            name = i.replace("Type", "")
            if name.startswith("device"):
                config["devices"][name] = data[i]

            elif name.startswith("sensor"):
                config["sensors"][name] = data[i]

    template = loader.get_template('node_configuration/configure-page2.html')

    print(json.dumps(config, indent=4))

    return HttpResponse(template.render({'context': config}, request))



def configure_page3(request):
    if request.method == "POST":
        data = json.loads(request.body.decode("utf-8"))
    else:
        raise Http404("ERROR: Must post data")

    print(json.dumps(data, indent=4))

    config = {}

    for i in data.keys():
        if i.startswith("deviceType") or i.startswith("sensorType"):
            name = i.replace("Type", "")
            config[name] = data[i]

    template = loader.get_template('node_configuration/configure-page3.html')

    print(json.dumps(config, indent=4))

    return HttpResponse(template.render({'context': config}, request))



def generateConfigFile(request):
    if request.method == "POST":
        data = json.loads(request.body.decode("utf-8"))
    else:
        raise Http404("ERROR: Must post data")

    try:
        # Check if file with identical parameters exists in database
        duplicate = Config.objects.get(config_file = CONFIG_DIR + data["friendlyName"] + ".json")

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

    # Iterate JSON and create section for each device and sensor
    for i in data.keys():
        if i.startswith("deviceType") or i.startswith("sensorType"):
            name = i.replace("Type", "")
            config[name] = {}
            config[name]["type"] = data[i]

            # Get all parameters that start with name, add to config section
            for j in data.keys():
                if j.startswith(name):
                    # Cast to int if possible (pin numbers, numeric rules, etc), otherwise keep string (enable/disable/on/off rules, IPs, etc)
                    try:
                        config[name][j[8:]] = int(data[j])
                    except ValueError:
                        config[name][j[8:]] = data[j]

            # Create empty sections, populated in loops below
            config[name]["schedule"] = {}

            if i.startswith("sensor"):
                config[name]["targets"] = []

    # Find targets, add to correct sensor's targets list
    for i in data.keys():
        if i.startswith("target"):
            n, sensor, target = i.split("-")
            config[sensor]["targets"].append(target)

    # Schedule rules
    for i in data.keys():
        if i.startswith("schedule") and i.endswith("time"):
            timestamp = data[i]
            instance = i.split("-")[1]

            # If user left timestamp blank, do not add rule and continue loop
            if len(timestamp) == 0: continue

            for j in data.keys():
                if j.startswith(i[:-5]) and j.endswith("value"):
                    # If user left rule blank, do not add rule and continue loop
                    if len(data[j]) == 0: continue

                    config[instance]["schedule"][timestamp] = data[j]

    print(json.dumps(data, indent=4))

    print(json.dumps(config, indent=4))

    with open(CONFIG_DIR + config["metadata"]["id"] + ".json", 'w') as file:
        json.dump(config, file)

    new = Config(config_file = CONFIG_DIR + config["metadata"]["id"] + ".json", uploaded = False)
    new.save()

    return JsonResponse("Config created.", safe=False, status=200)



def addSensor(request, count):
    template = loader.get_template('node_configuration/add-sensor.html')

    return HttpResponse(template.render({'context': count}, request))

def sensorOptionsPir(request, count):
    template = loader.get_template('node_configuration/pir-config.html')

    return HttpResponse(template.render({'context': count}, request))

def sensorOptionsSwitch(request, count):
    template = loader.get_template('node_configuration/switch-config.html')

    return HttpResponse(template.render({'context': count}, request))

def sensorOptionsDummy(request, count):
    template = loader.get_template('node_configuration/dummy-config.html')

    return HttpResponse(template.render({'context': count}, request))

def sensorOptionsDesktop(request, count):
    template = loader.get_template('node_configuration/desktop-config.html')

    return HttpResponse(template.render({'context': count}, request))

def sensorOptionsSi7021(request, count):
    template = loader.get_template('node_configuration/si7021-config.html')

    return HttpResponse(template.render({'context': count}, request))



def addDevice(request, count):
    template = loader.get_template('node_configuration/add-device.html')

    return HttpResponse(template.render({'context': count}, request))

def deviceOptionsDimmer(request, count):
    template = loader.get_template('node_configuration/dimmer-config.html')

    return HttpResponse(template.render({'context': count}, request))

def deviceOptionsBulb(request, count):
    template = loader.get_template('node_configuration/bulb-config.html')

    return HttpResponse(template.render({'context': count}, request))

def deviceOptionsRelay(request, count):
    template = loader.get_template('node_configuration/relay-config.html')

    return HttpResponse(template.render({'context': count}, request))

def deviceOptionsDumbRelay(request, count):
    template = loader.get_template('node_configuration/dumb-relay-config.html')

    return HttpResponse(template.render({'context': count}, request))

def deviceOptionsDesktop(request, count):
    template = loader.get_template('node_configuration/desktop-target-config.html')

    return HttpResponse(template.render({'context': count}, request))

def deviceOptionsPwm(request, count):
    template = loader.get_template('node_configuration/pwm-config.html')

    return HttpResponse(template.render({'context': count}, request))

def deviceOptionsMosfet(request, count):
    template = loader.get_template('node_configuration/mosfet-config.html')

    return HttpResponse(template.render({'context': count}, request))

def deviceOptionsApi(request, count):
    template = loader.get_template('node_configuration/api-target-config.html')

    return HttpResponse(template.render({'context': count}, request))
