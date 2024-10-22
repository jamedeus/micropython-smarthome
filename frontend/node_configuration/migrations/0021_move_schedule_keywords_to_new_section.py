# Generated by Django 4.2.16 on 2024-10-21 06:44

from django.db import migrations


def move_schedule_keywords_to_new_section(apps, schema_editor):
    Config = apps.get_model('node_configuration', 'Config')
    for config in Config.objects.all():
        # Copy schedule_keywords from metadata to new section, delete from metadata
        config.config['schedule_keywords'] = config.config['metadata']['schedule_keywords']
        del config.config['metadata']['schedule_keywords']
        config.save()


class Migration(migrations.Migration):

    dependencies = [
        ('node_configuration', '0020_add_desktop_trigger_mode_attribute'),
    ]

    operations = [
        migrations.RunPython(move_schedule_keywords_to_new_section)
    ]
