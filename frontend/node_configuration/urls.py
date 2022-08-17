from django.urls import path

from . import views

app_name = "node_configuration"

urlpatterns = [
    path('node_configuration', views.node_configuration, name='node_configuration'),

    # Argument is optional
    path('upload', views.upload, name='upload'),
    path('upload/<str:reupload>', views.upload, name='upload'),

    path('delete_config', views.delete_config, name='delete_config'),
    path('delete_node', views.delete_node, name='delete_node'),
    path('edit_config/<str:name>', views.edit_config, name='edit_config'),

    path('configure', views.configure, name='configure'),

    # Argument is optional
    path('generateConfigFile', views.generateConfigFile, name='generateConfigFile'),
    path('generateConfigFile/<str:edit_existing>', views.generateConfigFile, name='generateConfigFile'),
]
