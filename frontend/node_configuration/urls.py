from django.urls import path

from . import views

app_name = "node_configuration"

urlpatterns = [
    path('node_configuration', views.node_configuration, name='node_configuration'),

    # Allow accessing with relative path
    path('configure/setup', views.setup, name='setup'),
    path('edit_config/setup', views.setup, name='setup'),
    path('edit_config/upload', views.upload, name='upload'),
    path('edit_config/upload/<str:reupload>', views.upload, name='upload'),
    path('edit_config/generateConfigFile/<str:edit_existing>', views.generateConfigFile, name='generateConfigFile'),

    # Argument is optional
    path('upload', views.upload, name='upload'),
    path('upload/<str:reupload>', views.upload, name='upload'),
    path('reupload_all', views.reupload_all, name='reupload_all'),
    path('setup', views.setup, name='setup'),

    path('delete_config', views.delete_config, name='delete_config'),
    path('delete_node', views.delete_node, name='delete_node'),
    path('edit_config/<str:name>', views.edit_config, name='edit_config'),

    path('configure', views.configure, name='configure'),

    # Argument is optional
    path('generateConfigFile', views.generateConfigFile, name='generateConfigFile'),
    path('generateConfigFile/<str:edit_existing>', views.generateConfigFile, name='generateConfigFile'),

    path('set_default_credentials', views.set_default_credentials, name='set_default_credentials'),

    path('restore_config', views.restore_config, name='restore_config'),

    path('check_duplicate', views.check_duplicate, name='check_duplicate'),
]
