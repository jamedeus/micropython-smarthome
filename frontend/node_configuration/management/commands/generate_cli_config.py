'''Custom management command used to generate cli_config.json with current
database Node and ScheduleKeyword model contents.
'''

import os
import json
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from helper_functions import get_cli_config_name
from node_configuration.models import Node, ScheduleKeyword


# pylint: disable=line-too-long, missing-class-docstring
class Command(BaseCommand):
    help = 'Generate cli_config.json containing all nodes and schedule keywords from database'

    def handle(self, *args, **options):
        if not settings.CLI_SYNC:
            raise CommandError('Files cannot be written in diskless mode, set the CLI_SYNC env var to enable.')

        # Create cli_config template
        template = {
            "nodes": {},
            "schedule_keywords": {},
            "config_directory": settings.CONFIG_DIR,
            "webrepl_password": settings.NODE_PASSWD
        }

        # Add entry for each existing node with IP and config file path
        for node in Node.objects.all():
            config_name = get_cli_config_name(node.friendly_name)
            template["nodes"][config_name] = {
                "config": os.path.join(settings.CONFIG_DIR, node.config.filename),
                "ip": node.ip
            }

        # Add entry for each existing schedule keyword
        for keyword in ScheduleKeyword.objects.all():
            template["schedule_keywords"][keyword.keyword] = keyword.timestamp

        self.stdout.write("Generated config:")
        self.stdout.write(json.dumps(template, indent=4))

        # Write cli_config.json to disk
        cli_config = os.path.join(settings.REPO_DIR, "CLI", "cli_config.json")
        with open(cli_config, "w", encoding="utf-8") as file:
            json.dump(template, file)
