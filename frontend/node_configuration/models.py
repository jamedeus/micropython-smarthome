'''Django database models'''

from django.db import models, IntegrityError
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator


class TimeStampField(models.CharField):
    '''Custom database field used to store HH:MM timestamps.'''

    def __init__(self, *args, **kwargs):
        time_validator = RegexValidator(
            regex=r'^(0[0-9]|1[0-9]|2[0-3]):[0-5][0-9]$',
            message="Timestamp format must be HH:MM (no AM/PM)."
        )
        kwargs['max_length'] = 5
        kwargs['validators'] = [time_validator]
        super().__init__(*args, **kwargs)


class Node(models.Model):
    '''Tracks an ESP32 node and makes it accessible in the frontend.'''

    def __str__(self):
        return self.friendly_name

    friendly_name = models.CharField(max_length=50, unique=True)

    ip = models.GenericIPAddressField(protocol='IPv4')

    floor = models.IntegerField(
        default=1,
        validators=[MinValueValidator(-999), MaxValueValidator(999)]
    )

    # Validate all fields before saving
    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


class Config(models.Model):
    '''Stores JSON config file used by an ESP32 node, has reverse relation to
    Node entry once config file has been uploaded.
    '''

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

    # Validate all fields before saving
    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


class GpsCoordinates(models.Model):
    '''Stores latitude and longitude set by user, added to all config files
    (used by firmware to look up accurate sunrise and sunset times).
    '''

    def __str__(self):
        return self.display

    display = models.TextField()
    lat = models.DecimalField(max_digits=8, decimal_places=5)
    lon = models.DecimalField(max_digits=8, decimal_places=5)


class ScheduleKeyword(models.Model):
    '''Stores a schedule keyword and timestamp.'''

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
        return super().delete(*args, **kwargs)
