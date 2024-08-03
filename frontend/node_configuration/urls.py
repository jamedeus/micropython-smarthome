'''Map API endpoints to backend functions'''

from django.urls import path

from . import views

app_name = "node_configuration"

# pylint: disable=line-too-long
urlpatterns = [
    # Generate endpoint, must post form data
    # Optional argument contains name of existing node to overwrite
    path('generate_config_file', views.generate_config_file, name='generate_config_file'),
    path('generate_config_file/<str:edit_existing>', views.generate_config_file, name='generate_config_file'),

    # Post node name, returns bool
    path('check_duplicate', views.check_duplicate, name='check_duplicate'),

    # Config file management endpoints
    path('delete_config', views.delete_config, name='delete_config'),

    # Node management endpoints
    path('delete_node', views.delete_node, name='delete_node'),
    path('change_node_ip', views.change_node_ip, name='change_node_ip'),

    # Uploads config to node
    # Optional reupload arg prevents creating new model entry
    path('upload', views.upload, name='upload'),
    path('upload/<str:reupload>', views.upload, name='upload'),

    # Overview dropdown menu endpoints
    path('reupload_all', views.reupload_all, name='reupload_all'),
    path('restore_config', views.restore_config, name='restore_config'),
    path('get_location_suggestions/<str:query>', views.get_location_suggestions, name='get_location_suggestions'),
    path('set_default_location', views.set_default_location, name='set_default_location'),

    # Schedule keyword management endpoints
    path('add_schedule_keyword', views.add_schedule_keyword_config, name='add_schedule_keyword'),
    path('edit_schedule_keyword', views.edit_schedule_keyword_config, name='edit_schedule_keyword'),
    path('delete_schedule_keyword', views.delete_schedule_keyword_config, name='delete_schedule_keyword'),

    # Template views: overview, create new config, edit existing config
    path('config_overview', views.config_overview, name='config_overview'),
    path('new_config', views.new_config, name='new_config'),
    path('edit_config/<str:name>', views.edit_config, name='edit_config'),

    # Sync endpoints called by CLI tools
    path('get_nodes', views.get_nodes, name='get_nodes'),
    path('get_schedule_keywords', views.get_schedule_keywords, name='get_schedule_keywords'),
    path('get_node_config/<str:ip>', views.get_node_config, name='get_node_config'),
    path('add_node', views.add_node, name='add_node')
]
