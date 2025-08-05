from django.db import models

from libs.constants import DEFAULT_RATING, DEFAULT_RD, DEFAULT_VOLATILITY

from .team import Team


class GlickoRating(models.Model):
    """Glicko rating for a team in a specific season."""

    pk = models.CompositePrimaryKey("team_id", "season")
    team = models.ForeignKey(
        Team,
        on_delete=models.CASCADE,
        related_name="rating_history",
    )
    season = models.PositiveIntegerField()
    previous_rating = models.FloatField(default=DEFAULT_RATING)
    previous_rd = models.FloatField(default=DEFAULT_RD)
    previous_vol = models.FloatField(default=DEFAULT_VOLATILITY)
    rating = models.FloatField()
    rd = models.FloatField()
    vol = models.FloatField()
    rating_change = models.GeneratedField(
        output_field=models.FloatField(),
        expression=models.F("rating") - models.F("previous_rating"),
        db_persist=True,
    )

    class Meta:
        ordering = ["season", "team_id"]
        verbose_name = "glicko rating"
        verbose_name_plural = "glicko ratings"
        constraints = [
            models.UniqueConstraint(
                fields=["team", "season"],
                name="unique_team_glicko_rating_per_season",
            )
        ]
        indexes = [models.Index(fields=["team", "season"])]
