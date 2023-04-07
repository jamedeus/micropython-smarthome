from django.db import models
from django.conf import settings
import os, json



class Node(models.Model):

    def __str__(self):
        return self.friendly_name

    friendly_name = models.CharField(max_length=50)

    ip = models.GenericIPAddressField(protocol='IPv4')

    floor = models.IntegerField(default=1)



class Config(models.Model):

    def __str__(self):
        return self.filename

    # The actual config object
    config = models.JSONField(null=False, blank=False)

    filename = models.CharField(max_length=50, null=False, blank=False)

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



class WifiCredentials(models.Model):

    def __str__(self):
        return self.ssid

    ssid = models.TextField()
    password = models.TextField()
