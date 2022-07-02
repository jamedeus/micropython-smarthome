from django.urls import path

from . import views

app_name = "node_configuration"

urlpatterns = [
    path('upload', views.upload, name='upload'),
    path('delete_config', views.delete_config, name='delete_config'),

    path('node_configuration', views.node_configuration_index, name='node_configuration_index'),

    path('configure', views.configure, name='configure'),
    path('configure_page2', views.configure_page2, name='configure_page2'),
    path('configure_page3', views.configure_page3, name='configure_page3'),

    path('edit_config/<str:name>', views.edit_config, name='edit_config'),

    path('addSensor/<int:count>', views.addSensor, name='addSensor'),
    path('edit_config/addSensor/<int:count>', views.addSensor, name='addSensor'),

    path('sensorOptionsPir/<int:count>', views.sensorOptionsPir, name='sensorOptionsPir'),
    path('sensorOptionsSwitch/<int:count>', views.sensorOptionsSwitch, name='sensorOptionsSwitch'),
    path('sensorOptionsDummy/<int:count>', views.sensorOptionsDummy, name='sensorOptionsDummy'),
    path('sensorOptionsDesktop/<int:count>', views.sensorOptionsDesktop, name='sensorOptionsDesktop'),
    path('sensorOptionsSi7021/<int:count>', views.sensorOptionsSi7021, name='sensorOptionsSi7021'),

    path('addDevice/<int:count>', views.addDevice, name='addDevice'),
    path('edit_config/addDevice/<int:count>', views.addDevice, name='addDevice'),

    path('deviceOptionsDimmer/<int:count>', views.deviceOptionsDimmer, name='deviceOptionsDimmer'),
    path('deviceOptionsBulb/<int:count>', views.deviceOptionsBulb, name='deviceOptionsBulb'),
    path('deviceOptionsRelay/<int:count>', views.deviceOptionsRelay, name='deviceOptionsRelay'),
    path('deviceOptionsDumbRelay/<int:count>', views.deviceOptionsDumbRelay, name='deviceOptionsDumbRelay'),
    path('deviceOptionsDesktop/<int:count>', views.deviceOptionsDesktop, name='deviceOptionsDesktop'),
    path('deviceOptionsPwm/<int:count>', views.deviceOptionsPwm, name='deviceOptionsPwm'),
    path('deviceOptionsMosfet/<int:count>', views.deviceOptionsMosfet, name='deviceOptionsMosfet'),
    path('deviceOptionsApi/<int:count>', views.deviceOptionsApi, name='deviceOptionsApi'),

    # Argument is optional
    path('generateConfigFile', views.generateConfigFile, name='generateConfigFile'),
    path('generateConfigFile/<str:edit_existing>', views.generateConfigFile, name='generateConfigFile'),
]
