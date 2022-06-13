from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponse, Http404, JsonResponse, FileResponse
from django.template import loader
import json



def configure(request):
    template = loader.get_template('node_configuration/configure.html')

    return HttpResponse(template.render({}, request))



def generateConfigFile(request):
    if request.method == "POST":
        data = json.loads(request.body.decode("utf-8"))
    else:
        raise Http404("ERROR: Must post data")

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

    for i in data.keys():
        if (i.startswith("device") and i.endswith("type")) or (i.startswith("sensor") and i.endswith("type")):
            name = i[0:7]
            config[name] = {}

            for j in data.keys():
                if j.startswith(name):
                    config[name][j[8:]] = data[j]

            config[name]["schedule"] = {}

            if i.startswith("sensor"):
                config[name]["targets"] = []

    print(json.dumps(data, indent=4))

    print(json.dumps(config, indent=4))

    return HttpResponse('')


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
