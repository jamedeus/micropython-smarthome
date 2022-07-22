from django.urls import path

from . import views

app_name = "api"

urlpatterns = [
    path('get_status/<str:node>', views.get_status, name='get_status'),
    path('get_climate_data/<str:node>', views.get_climate_data, name='get_climate_data'),
    path('send_command', views.send_command, name='send_command'),

    # Change view name
    path('api', views.api_overview, name='api_overview'),
    path('api/<str:node>', views.api, name='api'),

    path('legacy_api', views.legacy_api, name='legacy_api'),
]
