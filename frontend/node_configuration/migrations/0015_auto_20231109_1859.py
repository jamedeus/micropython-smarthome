# Generated by Django 4.0.4 on 2023-11-10 02:59

import json
from django.db import migrations
from django.conf import settings


# Add units key to thermostat instances in all existing config files
def add_units(apps, schema_editor):
    Config = apps.get_model('node_configuration', 'Config')
    for config in Config.objects.all():
        for i in config.config:
            if not i.startswith('sensor'): continue
            if not config.config[i]['_type'] in ['si7021', 'dht22']: continue

            config.config[i]['units'] = 'fahrenheit'
        config.save()


def update_config_on_disk(apps, scheda_editor):
    Config = apps.get_model('node_configuration', 'Config')
    for config in Config.objects.all():
        with open(settings.CONFIG_DIR + config.filename, 'w') as file:
            json.dump(config.config, file)


class Migration(migrations.Migration):

    dependencies = [
        ('node_configuration', '0014_auto_20231014_0251'),
    ]

    operations = [
        migrations.RunPython(add_units),
        migrations.RunPython(update_config_on_disk)
    ]
