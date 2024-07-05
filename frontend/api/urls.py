from django.urls import path

from . import views

app_name = "api"

urlpatterns = [
    # API call views
    path('get_status/<str:node>', views.get_status, name='get_status'),
    path('get_climate_data/<str:node>', views.get_climate_data, name='get_climate_data'),
    path('send_command', views.send_command, name='send_command'),
    path('reboot_all', views.reboot_all, name='reboot_all'),
    path('reset_all', views.reset_all, name='reset_all'),
    path('sync_schedule_keywords', views.sync_schedule_keywords, name='sync_schedule_keywords'),
    path('sync_schedule_rules', views.sync_schedule_rules, name='sync_schedule_rules'),

    # Macro views
    path('run_macro/<str:name>', views.run_macro, name='run_macro'),
    path('add_macro_action', views.add_macro_action, name='add_macro_action'),
    path('delete_macro/<str:name>', views.delete_macro, name='delete_macro'),
    path('delete_macro_action/<str:name>/<int:index>', views.delete_macro_action, name='delete_macro_action'),
    path('macro_name_available/<str:name>', views.macro_name_available, name='macro_name_available'),
    path('skip_instructions', views.skip_instructions, name='skip_instructions'),

    # IR macro views
    path('edit_ir_macro', views.edit_ir_macro, name='edit_ir_macro'),
    path('add_ir_macro', views.add_ir_macro, name='add_ir_macro'),

    # Template views
    path('', views.api_overview, name='api_overview'),
    path('api', views.api_overview, name='api_overview'),
    path('api/recording/<str:recording>', views.api_overview, name='api_overview'),
    path('api/<str:node>', views.api, name='api'),
    path('api/<str:node>/<str:recording>', views.api, name='api')
]
