from django.db import models

from core.models.venue import Venue


class Team(models.Model):
    """
    Represents a sports team.
    """

    school = models.CharField(max_length=200)
    mascot = models.CharField(max_length=100, null=True, blank=True)
    abbreviation = models.CharField(max_length=20, null=True, blank=True)
    conference = models.CharField(max_length=100, null=True, blank=True)
    division = models.CharField(max_length=100)
    classification = models.CharField(max_length=100, null=True, blank=True)
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

    def __str__(self):
        return f"{self.school} {self.mascot} ({self.abbreviation})"


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

    def __str__(self):
        return f"{self.name} ({self.team.abbreviation})"


class TeamLogo(models.Model):
    """
    Stores logo URLs for a team.
    """

    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="logos")
    url = models.URLField()

    def __str__(self):
        return f"Logo for {self.team.abbreviation}: {self.url}"
