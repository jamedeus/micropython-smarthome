from django.core.management.base import BaseCommand
from node_configuration.models import Config


class Command(BaseCommand):
    help = 'Iterate config files in database and create a file in CONFIG_DIR for each'

    def handle(self, *args, **options):
        for config in Config.objects.all():
            self.stdout.write(f'Exporting {config.filename}')
            config.write_to_disk()
