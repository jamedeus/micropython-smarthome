from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponse, Http404, JsonResponse, FileResponse
from django.template import loader
import json
import os

from .models import Node, Config

CONFIG_DIR = "/home/jamedeus/git/micropython-smarthome/config/"



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
        if i.endswith("type"):
            name = i[0:7]
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
        if i.endswith("type"):
            name = i[0:7]
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
        # Match both start and end to avoid adding duplicates
        if (i.startswith("device") and i.endswith("type")) or (i.startswith("sensor") and i.endswith("type")):
            name = i[0:7]
            config[name] = {}

            # Get all parameters that start with name, add to config section
            for j in data.keys():
                if j.startswith(name):
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
