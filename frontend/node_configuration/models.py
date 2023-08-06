import os
import json
from django.conf import settings
from django.dispatch import receiver
from django.db import models, IntegrityError
from django.db.models.signals import post_save, post_delete
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator
from helper_functions import get_schedule_keywords_dict, get_cli_config, add_node_to_cli_config, write_cli_config


class TimeStampField(models.CharField):
    def __init__(self, *args, **kwargs):
        time_validator = RegexValidator(
            regex=r'^(0[0-9]|1[0-9]|2[0-3]):[0-5][0-9]$',
            message="Timestamp format must be HH:MM (no AM/PM)."
        )
        kwargs['max_length'] = 5
        kwargs['validators'] = [time_validator]
        super().__init__(*args, **kwargs)


class Node(models.Model):
    def __str__(self):
        return self.friendly_name

    friendly_name = models.CharField(max_length=50, unique=True)

    ip = models.GenericIPAddressField(protocol='IPv4')

    floor = models.IntegerField(default=1, validators=[MinValueValidator(0), MaxValueValidator(999)])

    # Validate all fields before saving
    # Add to cli_config.json if CLI_SYNC enabled
    def save(self, *args, **kwargs):
        self.full_clean()
        if settings.CLI_SYNC and hasattr(self, 'config'):
            config_path = os.path.join(settings.CONFIG_DIR, self.config.filename)
            add_node_to_cli_config(self.friendly_name, config_path, self.ip)
        return super().save(*args, **kwargs)

    # Remove from cli_config.json if CLI_SYNC enabled
    def delete(self, *args, **kwargs):
        if settings.CLI_SYNC:
            try:
                cli_config = get_cli_config()
                del cli_config['nodes'][self.friendly_name]
                write_cli_config(cli_config)
            except KeyError:
                pass
        return super().delete(*args, **kwargs)


class Config(models.Model):
    def __str__(self):
        return self.filename

    # The actual config object
    config = models.JSONField(null=False, blank=False)

    filename = models.CharField(max_length=50, null=False, blank=False, unique=True)

    node = models.OneToOneField(
        Node,
        on_delete=models.CASCADE,
        related_name='config',
        null=True,
        blank=True
    )

    def read_from_disk(self):
        if settings.CLI_SYNC:
            with open(os.path.join(settings.CONFIG_DIR, self.filename), 'r') as file:
                self.config = json.load(file)
                self.save()
        else:
            print('WARNING: read_from_disk called with CLI_SYNC disabled, ignoring.')

    def write_to_disk(self):
        if settings.CLI_SYNC:
            # Write config file to disk
            with open(os.path.join(settings.CONFIG_DIR, self.filename), 'w') as file:
                json.dump(self.config, file)

            # Add to cli_config.json
            if self.node:
                add_node_to_cli_config(
                    self.node.friendly_name,
                    os.path.join(settings.CONFIG_DIR, self.filename),
                    self.node.ip
                )
        else:
            print('WARNING: write_to_disk called with CLI_SYNC disabled, ignoring.')

    # Validate all fields before saving
    def save(self, *args, **kwargs):
        self.full_clean()

        # Write to disk if CLI_SYNC enabled
        if settings.CLI_SYNC:
            self.write_to_disk()

        return super().save(*args, **kwargs)


# TODO fix cleartext password
class WifiCredentials(models.Model):
    def __str__(self):
        return self.ssid

    ssid = models.TextField()
    password = models.TextField()


class GpsCoordinates(models.Model):
    def __str__(self):
        return self.display

    display = models.TextField()
    lat = models.DecimalField(max_digits=8, decimal_places=5)
    lon = models.DecimalField(max_digits=8, decimal_places=5)


class ScheduleKeyword(models.Model):
    def __str__(self):
        return self.keyword

    keyword = models.CharField(max_length=50, unique=True, null=False, blank=False)

    timestamp = TimeStampField()

    # Validate all fields before saving
    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    # Prevent deleting sunrise or sunset
    def delete(self, *args, **kwargs):
        if self.keyword in ["sunrise", "sunset"]:
            raise IntegrityError(f"{self.keyword} is required and cannot be deleted")
        else:
            return super().delete(*args, **kwargs)


# Write schedule keywords to json file when modified (sync with CLI client)
@receiver(post_save, sender=ScheduleKeyword)
@receiver(post_delete, sender=ScheduleKeyword)
def write_to_disk(**kwargs):
    if settings.CLI_SYNC:
        config = get_cli_config()
        config['schedule_keywords'] = get_schedule_keywords_dict()
        with open(os.path.join(settings.REPO_DIR, 'CLI', 'cli_config.json'), 'w') as file:
            json.dump(config, file)
