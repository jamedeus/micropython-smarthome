from django.urls import path

from . import views

app_name = "node_configuration"

urlpatterns = [
    path('configure', views.configure, name='configure'),

    path('addSensor/<int:count>', views.addSensor, name='addSensor'),

    path('sensorOptionsPir/<int:count>', views.sensorOptionsPir, name='sensorOptionsPir'),
    path('sensorOptionsSwitch/<int:count>', views.sensorOptionsSwitch, name='sensorOptionsSwitch'),
    path('sensorOptionsDummy/<int:count>', views.sensorOptionsDummy, name='sensorOptionsDummy'),
    path('sensorOptionsDesktop/<int:count>', views.sensorOptionsDesktop, name='sensorOptionsDesktop'),
    path('sensorOptionsSi7021/<int:count>', views.sensorOptionsSi7021, name='sensorOptionsSi7021'),

    path('addDevice/<int:count>', views.addDevice, name='addDevice'),

    path('deviceOptionsDimmer/<int:count>', views.deviceOptionsDimmer, name='deviceOptionsDimmer'),
    path('deviceOptionsBulb/<int:count>', views.deviceOptionsBulb, name='deviceOptionsBulb'),
    path('deviceOptionsRelay/<int:count>', views.deviceOptionsRelay, name='deviceOptionsRelay'),
    path('deviceOptionsDumbRelay/<int:count>', views.deviceOptionsDumbRelay, name='deviceOptionsDumbRelay'),
    path('deviceOptionsDesktop/<int:count>', views.deviceOptionsDesktop, name='deviceOptionsDesktop'),
    path('deviceOptionsPwm/<int:count>', views.deviceOptionsPwm, name='deviceOptionsPwm'),
    path('deviceOptionsMosfet/<int:count>', views.deviceOptionsMosfet, name='deviceOptionsMosfet'),
    path('deviceOptionsApi/<int:count>', views.deviceOptionsApi, name='deviceOptionsApi'),

    path('generateConfigFile', views.generateConfigFile, name='generateConfigFile'),
]
