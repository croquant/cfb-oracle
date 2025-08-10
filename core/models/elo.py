"""Elo rating model for tracking team performance."""

from django.db import models

from libs.constants import DEFAULT_RATING

from .match import Match
from .team import Team


class EloRating(models.Model):
    """Elo rating for a team before and after a specific match."""

    team = models.ForeignKey(
        Team,
        on_delete=models.CASCADE,
        related_name="elo_ratings",
    )
    match = models.ForeignKey(
        Match,
        on_delete=models.CASCADE,
        related_name="elo_ratings",
    )
    rating_before = models.FloatField(default=DEFAULT_RATING)
    rating_after = models.FloatField()
    rating_change = models.GeneratedField(
        output_field=models.FloatField(),
        expression=models.F("rating_after") - models.F("rating_before"),
        db_persist=True,
    )

    class Meta:
        """Metadata for EloRating model."""

        ordering = ["match_id", "team_id"]
        verbose_name = "elo rating"
        verbose_name_plural = "elo ratings"
        constraints = [
            models.UniqueConstraint(
                fields=["team", "match"],
                name="unique_team_elo_per_match",
            )
        ]
        indexes = [models.Index(fields=["team", "match"])]

    def __str__(self) -> str:
        """Return the rating for display."""
        return (
            f"{self.match.season}-{self.match.week} "
            f"{self.team}: {self.rating_after}"
        )
