from django.db import models


class Venue(models.Model):
    """
    Represents a venue or stadium.
    """

    name = models.CharField(max_length=200)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    zip_code = models.CharField(max_length=20, null=True, blank=True)
    country_code = models.CharField(max_length=3, null=True, blank=True)
    timezone = models.CharField(max_length=50, null=True, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    elevation = models.CharField(max_length=50, null=True, blank=True)
    capacity = models.IntegerField(null=True, blank=True)
    construction_year = models.IntegerField(null=True, blank=True)
    grass = models.BooleanField(null=True, blank=True)
    dome = models.BooleanField(null=True, blank=True)

    def __str__(self):
        return f"{self.name} ({self.city}, {self.state})"

    class Meta:
        ordering = ["name"]
