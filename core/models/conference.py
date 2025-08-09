from django.db import models
from django.utils.text import slugify

from core.models.enums import DivisionClassification


class Conference(models.Model):
    """Represents an athletic conference."""

    name = models.CharField(max_length=200)
    short_name = models.CharField(max_length=100, blank=True)
    abbreviation = models.CharField(max_length=20, blank=True)
    slug = models.SlugField(max_length=50, unique=True)
    classification = models.CharField(
        max_length=10,
        choices=DivisionClassification.choices,
        blank=True,
    )

    class Meta:
        ordering = ["name"]
        verbose_name = "conference"
        verbose_name_plural = "conferences"

    def __str__(self) -> str:
        return self.name

    def save(self, *args: object, **kwargs: object) -> None:
        if (
            not self.slug
            or self.slug == ""
            or slugify(self.name) not in self.slug
        ):
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            while Conference.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)
