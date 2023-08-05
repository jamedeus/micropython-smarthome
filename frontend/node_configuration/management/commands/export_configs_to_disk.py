from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from node_configuration.models import Config


class Command(BaseCommand):
    help = 'Iterate config files in database and create a file in CONFIG_DIR for each'

    def handle(self, *args, **options):
        if not settings.CLI_SYNC:
            raise CommandError('Files cannot be written in diskless mode, set the CLI_SYNC env var to enable.')

        for config in Config.objects.all():
            self.stdout.write(f'Exporting {config.filename}')
            config.write_to_disk()
