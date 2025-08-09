from django.db import models
from django.utils.text import slugify

from core.models.conference import Conference
from core.models.enums import DivisionClassification
from core.models.venue import Venue


class TeamQuerySet(models.QuerySet):
    """Custom ``QuerySet`` for :class:`Team`.

    Provides a helper to prefetch related ``logos`` and
    ``alternative_names`` to avoid N+1 queries.
    """

    def with_related(self) -> "TeamQuerySet":
        """Prefetch logos and alternative names."""
        return self.select_related("conference", "location").prefetch_related(
            "logos", "alternative_names"
        )


class TeamManager(models.Manager):
    """Manager that always prefetches team metadata."""

    def get_queryset(self) -> "TeamQuerySet":
        return TeamQuerySet(self.model, using=self._db).with_related()

    def with_related(self) -> "TeamQuerySet":
        return self.get_queryset()


class Team(models.Model):
    """Represents a sports team and its related metadata.

    The default manager automatically prefetches ``logos`` and
    ``alternative_names`` to keep database queries constant. The
    ``logo_bright`` and ``logo_dark`` properties expose the first two logo
    URLs for convenient front-end access.
    """

    school = models.CharField(max_length=200)
    mascot = models.CharField(max_length=100, blank=True)
    abbreviation = models.CharField(max_length=20, blank=True)
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
        blank=True,
    )
    color = models.CharField(max_length=20)
    alternate_color = models.CharField(max_length=20)
    twitter = models.CharField(max_length=100, blank=True)
    location = models.ForeignKey(
        Venue,
        on_delete=models.SET_NULL,
        related_name="teams",
        null=True,
        blank=True,
    )
    active = models.BooleanField(default=True)

    objects = TeamManager()

    class Meta:
        ordering = ["school"]
        verbose_name = "team"
        verbose_name_plural = "teams"

    def __str__(self) -> str:
        mascot = f" {self.mascot}" if self.mascot else ""
        return f"{self.school}{mascot}"

    def save(self, *args: object, **kwargs: object) -> None:
        if (
            not self.slug
            or self.slug == ""
            or slugify(self.school) not in self.slug
        ):
            base_slug = slugify(self.school)
            slug = base_slug
            counter = 1
            while Team.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    @property
    def logo_bright(self) -> str | None:
        """Return the first logo URL if available."""
        logos = list(self.logos.all()[:1])
        return logos[0].url if logos else None

    @property
    def logo_dark(self) -> str | None:
        """Return the second logo URL if available."""
        logos = list(self.logos.all()[:2])
        return logos[1].url if len(logos) > 1 else None


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

    def __str__(self) -> str:
        return f"{self.name} ({self.team.school})"


class TeamLogo(models.Model):
    """Stores logo URLs for a team."""

    team = models.ForeignKey(
        Team,
        on_delete=models.CASCADE,
        related_name="logos",
    )
    url = models.URLField()

    class Meta:
        verbose_name = "team logo"
        verbose_name_plural = "team logos"

    def __str__(self) -> str:
        return f"Logo for {self.team.school}: {self.url}"
