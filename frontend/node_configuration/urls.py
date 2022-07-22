from django.urls import path

from . import views

app_name = "node_configuration"

urlpatterns = [
    path('node_configuration', views.node_configuration_index, name='node_configuration_index'),

    # Argument is optional
    path('upload', views.upload, name='upload'),
    path('upload/<str:reupload>', views.upload, name='upload'),

    path('delete_config', views.delete_config, name='delete_config'),
    path('edit_config/<str:name>', views.edit_config, name='edit_config'),

    path('configure', views.configure, name='configure'),
    path('configure_page2', views.configure_page2, name='configure_page2'),
    path('configure_page3', views.configure_page3, name='configure_page3'),

    # Argument is optional
    path('generateConfigFile', views.generateConfigFile, name='generateConfigFile'),
    path('generateConfigFile/<str:edit_existing>', views.generateConfigFile, name='generateConfigFile'),
]
