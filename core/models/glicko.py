"""Glicko rating model for tracking team performance."""

from django.db import models

from libs.constants import DEFAULT_RATING, DEFAULT_RD, DEFAULT_VOLATILITY

from .conference import Conference
from .enums import DivisionClassification
from .team import Team


class GlickoRating(models.Model):
    """Glicko rating for a team in a specific season and week."""

    pk = models.CompositePrimaryKey("team_id", "season", "week")
    team = models.ForeignKey(
        Team,
        on_delete=models.CASCADE,
        related_name="rating_history",
    )
    season = models.PositiveIntegerField(db_index=True)
    week = models.PositiveIntegerField(db_index=True)
    classification = models.CharField(
        max_length=20,
        choices=DivisionClassification.choices,
        blank=True,
        db_index=True,
    )
    conference = models.ForeignKey(
        Conference,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="glicko_ratings",
        db_index=True,
    )
    previous_rating = models.FloatField(default=DEFAULT_RATING)
    previous_rd = models.FloatField(default=DEFAULT_RD)
    previous_vol = models.FloatField(default=DEFAULT_VOLATILITY)
    rating = models.FloatField()
    rd = models.FloatField()
    vol = models.FloatField()
    active = models.BooleanField(default=False)
    rating_change = models.GeneratedField(
        output_field=models.FloatField(),
        expression=models.F("rating") - models.F("previous_rating"),
        db_persist=True,
    )

    class Meta:
        """Metadata for GlickoRating model."""

        ordering = ["season", "week", "team_id"]
        verbose_name = "glicko rating"
        verbose_name_plural = "glicko ratings"
        constraints = [
            models.UniqueConstraint(
                fields=["team", "season", "week"],
                name="unique_team_glicko_rating_per_week",
            )
        ]
        indexes = [models.Index(fields=["team", "season", "week"])]

    def __str__(self) -> str:
        """Return the rating for display."""
        return f"{self.season}-{self.week} {self.team}: {self.rating}"
