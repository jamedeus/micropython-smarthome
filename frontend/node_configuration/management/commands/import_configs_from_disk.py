'''Custom management command used to overwrite all config files in database
with contents of corresponding JSON files in CONFIG_DIR.
'''

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from node_configuration.models import Config


# pylint: disable=line-too-long, missing-class-docstring
class Command(BaseCommand):
    help = 'Overwrite all config files in database with corresponding files in CONFIG_DIR'

    def handle(self, *args, **options):
        if not settings.CLI_SYNC:
            raise CommandError('Files cannot be read in diskless mode, set the CLI_SYNC env var to enable.')

        for config in Config.objects.all():
            self.stdout.write(f'Importing {config.filename}')
            config.read_from_disk()
