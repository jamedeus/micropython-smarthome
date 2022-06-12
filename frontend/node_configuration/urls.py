from django.urls import path

from . import views

app_name = "node_configuration"

urlpatterns = [
    path('configure', views.configure, name='configure'),
    path('sensorOptionsPir', views.sensorOptionsPir, name='sensorOptionsPir'),
    path('sensorOptionsSwitch', views.sensorOptionsSwitch, name='sensorOptionsSwitch'),
    path('sensorOptionsDummy', views.sensorOptionsDummy, name='sensorOptionsDummy'),
    path('sensorOptionsDesktop', views.sensorOptionsDesktop, name='sensorOptionsDesktop'),
    path('sensorOptionsSi7021', views.sensorOptionsSi7021, name='sensorOptionsSi7021')
]
