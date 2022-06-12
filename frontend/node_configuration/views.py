from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponse, Http404, JsonResponse, FileResponse
from django.template import loader



def configure(request):
    template = loader.get_template('node_configuration/configure.html')

    return HttpResponse(template.render({}, request))

def sensorOptionsPir(request):
    template = loader.get_template('node_configuration/pir-config.html')

    return HttpResponse(template.render({}, request))

def sensorOptionsSwitch(request):
    template = loader.get_template('node_configuration/switch-config.html')

    return HttpResponse(template.render({}, request))

def sensorOptionsDummy(request):
    template = loader.get_template('node_configuration/dummy-config.html')

    return HttpResponse(template.render({}, request))

def sensorOptionsDesktop(request):
    template = loader.get_template('node_configuration/desktop-config.html')

    return HttpResponse(template.render({}, request))

def sensorOptionsSi7021(request):
    template = loader.get_template('node_configuration/si7021-config.html')

    return HttpResponse(template.render({}, request))
