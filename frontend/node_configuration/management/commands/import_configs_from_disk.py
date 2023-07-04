from django.core.management.base import BaseCommand
from node_configuration.models import Config


class Command(BaseCommand):
    help = 'Overwrite all config files in database with corresponding files in CONFIG_DIR'

    def handle(self, *args, **options):
        for config in Config.objects.all():
            self.stdout.write(f'Importing {config.filename}')
            config.read_from_disk()
