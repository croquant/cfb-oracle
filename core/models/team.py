from django.db import models
from django.utils.text import slugify

from core.models.conference import Conference
from core.models.enums import DivisionClassification
from core.models.venue import Venue


class Team(models.Model):
    """
    Represents a sports team.
    """

    school = models.CharField(max_length=200)
    mascot = models.CharField(max_length=100, null=True, blank=True)
    abbreviation = models.CharField(max_length=20, null=True, blank=True)
    slug = models.SlugField(max_length=50, unique=True)
    conference = models.ForeignKey(
        Conference,
        on_delete=models.SET_NULL,
        related_name="teams",
        null=True,
        blank=True,
    )
    classification = models.CharField(
        max_length=100,
        choices=DivisionClassification.choices,
        null=True,
        blank=True,
    )
    color = models.CharField(max_length=20)
    alternate_color = models.CharField(max_length=20)
    twitter = models.CharField(max_length=100, null=True, blank=True)
    location = models.ForeignKey(
        Venue,
        on_delete=models.SET_NULL,
        related_name="teams",
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ["school"]
        verbose_name = "team"
        verbose_name_plural = "teams"

    def __str__(self):
        mascot = f" {self.mascot}" if self.mascot else ""
        return f"{self.school}{mascot}"

    def save(self, *args, **kwargs):
        if not self.slug or self.slug == "" or slugify(self.school) not in self.slug:
            base_slug = slugify(self.school)
            slug = base_slug
            counter = 1
            while Team.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)


class TeamAlternativeName(models.Model):
    """
    Stores alternative names for a team.
    """

    team = models.ForeignKey(
        Team, on_delete=models.CASCADE, related_name="alternative_names"
    )
    name = models.CharField(max_length=200)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["team", "name"],
                name="team_name_unique",
            )
        ]
        verbose_name = "team alternative name"
        verbose_name_plural = "team alternative names"

    def __str__(self):
        return f"{self.name} ({self.team.school})"


class TeamLogo(models.Model):
    """
    Stores logo URLs for a team.
    """

    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="logos")
    url = models.URLField()

    def __str__(self):
        return f"Logo for {self.team.school}: {self.url}"

    class Meta:
        verbose_name = "team logo"
        verbose_name_plural = "team logos"
