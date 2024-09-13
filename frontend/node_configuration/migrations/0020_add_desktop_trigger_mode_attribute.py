# Generated by Django 4.2.15 on 2024-09-13 02:30

from django.db import migrations


def add_desktop_trigger_mode_attribute(apps, schema_editor):
    Config = apps.get_model('node_configuration', 'Config')
    for config in Config.objects.all():
        for i in config.config:
            # Skip irrelevant instances, instances that already have mode attribute
            if not i.startswith('sensor'):
                continue
            if not config.config[i]['_type'] == 'desktop':
                continue
            if 'mode' in config.config[i].keys():
                continue

            # Add mode key, default to screen (old behavior)
            config.config[i]['mode'] = 'screen'
        config.save()


class Migration(migrations.Migration):

    dependencies = [
        ('node_configuration', '0019_update_ir_target_names_in_existing_config_files'),
    ]

    operations = [
        migrations.RunPython(add_desktop_trigger_mode_attribute)
    ]
