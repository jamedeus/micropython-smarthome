from django.urls import path

from . import views

app_name = "pwa"

urlpatterns = [
    path('offline/', views.offline, name='offline'),
]
