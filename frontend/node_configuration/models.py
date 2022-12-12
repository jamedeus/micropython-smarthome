from django.db import models
import os

CONFIG_DIR = os.environ.get('CONFIG_DIR')



class Node(models.Model):

    def __str__(self):
        return self.friendly_name

    friendly_name = models.CharField(max_length=50)

    ip = models.GenericIPAddressField(protocol='IPv4')

    floor = models.IntegerField(default=1)

    config_file = models.FilePathField(path=CONFIG_DIR)



class Config(models.Model):

    def __str__(self):
        return self.config_file

    config_file = models.FilePathField(path=CONFIG_DIR)

    uploaded = models.BooleanField(default=False)



class WifiCredentials(models.Model):

    def __str__(self):
        return self.ssid

    ssid = models.TextField()
    password = models.TextField()
