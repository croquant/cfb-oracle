from django.db import models


class Venue(models.Model):
    """
    Represents a venue or stadium.
    """

    name = models.CharField(max_length=200)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    zip_code = models.CharField(max_length=20, blank=True)
    country_code = models.CharField(max_length=3, blank=True)
    timezone = models.CharField(max_length=50, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    elevation = models.FloatField(null=True, blank=True)
    capacity = models.IntegerField(null=True, blank=True)
    construction_year = models.IntegerField(null=True, blank=True)
    grass = models.BooleanField(null=True, blank=True)
    dome = models.BooleanField(null=True, blank=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "venue"
        verbose_name_plural = "venues"

    def __str__(self) -> str:
        return f"{self.name} ({self.city}, {self.state})"
