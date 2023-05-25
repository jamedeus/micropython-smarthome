from django.contrib import admin

from .models import Node, Config

admin.site.register(Node)
admin.site.register(Config)
