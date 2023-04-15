from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
import os, json



class Node(models.Model):

    def __str__(self):
        return self.friendly_name

    friendly_name = models.CharField(max_length=50, unique=True)

    ip = models.GenericIPAddressField(protocol='IPv4')

    floor = models.IntegerField(default=1, validators=[MinValueValidator(0), MaxValueValidator(999)])

    # Validate all fields before saving
    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)



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
        with open(settings.CONFIG_DIR + self.filename, 'r') as file:
            self.config = json.load(file)
            self.save()

    def write_to_disk(self):
        with open(settings.CONFIG_DIR + self.filename, 'w') as file:
            json.dump(self.config, file)

    # Validate all fields before saving
    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)



class WifiCredentials(models.Model):

    def __str__(self):
        return self.ssid

    ssid = models.TextField()
    password = models.TextField()
