from django.db import models

from core.models.conference import Conference
from core.models.enums import DivisionClassification, SeasonType
from core.models.team import Team
from core.models.venue import Venue


class Match(models.Model):
    """
    Represents a football match between two teams.

    The 'completed_requires_scores' constraint ensures that if a match is marked as completed,
    both home_score and away_score must be provided (not null). If the match is not completed,
    scores may be null.
    """

    season = models.PositiveIntegerField()
    week = models.PositiveIntegerField()
    season_type = models.CharField(
        max_length=20,
        choices=SeasonType.choices,
    )
    start_date = models.DateTimeField()
    completed = models.BooleanField(default=False)
    venue = models.ForeignKey(
        Venue, on_delete=models.SET_NULL, null=True, blank=True, related_name="matches"
    )
    neutral_site = models.BooleanField(default=False)
    attendance = models.PositiveIntegerField(blank=True, null=True)

    home_team = models.ForeignKey(
        Team, related_name="home_matches", on_delete=models.CASCADE
    )
    home_classification = models.CharField(
        max_length=20,
        choices=DivisionClassification.choices,
        null=True,
        blank=True,
    )
    home_conference = models.ForeignKey(
        Conference,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="home_matches",
    )
    home_score = models.PositiveIntegerField(blank=True, null=True)

    away_team = models.ForeignKey(
        Team, related_name="away_matches", on_delete=models.CASCADE
    )
    away_classification = models.CharField(
        max_length=20,
        choices=DivisionClassification.choices,
        null=True,
        blank=True,
    )
    away_conference = models.ForeignKey(
        Conference,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="away_matches",
    )
    away_score = models.PositiveIntegerField(blank=True, null=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=(
                    models.Q(completed=False)
                    | (
                        models.Q(completed=True)
                        & models.Q(home_score__isnull=False)
                        & models.Q(away_score__isnull=False)
                    )
                ),
                name="completed_requires_scores",
            )
        ]
        ordering = ["-start_date"]

    def __str__(self):
        return f"{self.home_team} vs {self.away_team} on {self.start_date}"
