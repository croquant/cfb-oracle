from django.db import models

from core.models.enums import DivisionClassification


class Conference(models.Model):
    """Represents an athletic conference."""

    name = models.CharField(max_length=200)
    short_name = models.CharField(max_length=100, null=True, blank=True)
    abbreviation = models.CharField(max_length=20, null=True, blank=True)
    classification = models.CharField(
        max_length=10,
        choices=DivisionClassification.choices,
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ["name"]
        verbose_name = "conference"
        verbose_name_plural = "conferences"

    def __str__(self) -> str:
        return self.name
