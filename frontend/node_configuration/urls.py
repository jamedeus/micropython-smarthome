from django.urls import path

from . import views

app_name = "node_configuration"

urlpatterns = [
    path('configure', views.configure, name='configure'),
    path('sensorOptionsPir', views.sensorOptionsPir, name='sensorOptionsPir'),
    path('sensorOptionsSwitch', views.sensorOptionsSwitch, name='sensorOptionsSwitch'),
    path('sensorOptionsDummy', views.sensorOptionsDummy, name='sensorOptionsDummy'),
    path('sensorOptionsDesktop', views.sensorOptionsDesktop, name='sensorOptionsDesktop'),
    path('sensorOptionsSi7021', views.sensorOptionsSi7021, name='sensorOptionsSi7021'),

    path('deviceOptionsDimmer', views.deviceOptionsDimmer, name='deviceOptionsDimmer'),
    path('deviceOptionsBulb', views.deviceOptionsBulb, name='deviceOptionsBulb'),
    path('deviceOptionsRelay', views.deviceOptionsRelay, name='deviceOptionsRelay'),
    path('deviceOptionsDumbRelay', views.deviceOptionsDumbRelay, name='deviceOptionsDumbRelay'),
    path('deviceOptionsDesktop', views.deviceOptionsDesktop, name='deviceOptionsDesktop'),
    path('deviceOptionsPwm', views.deviceOptionsPwm, name='deviceOptionsPwm'),
    path('deviceOptionsMosfet', views.deviceOptionsMosfet, name='deviceOptionsMosfet'),
    path('deviceOptionsApi', views.deviceOptionsApi, name='deviceOptionsApi'),
]
