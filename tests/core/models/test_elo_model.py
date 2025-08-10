"""Tests for the :class:`EloRating` model."""

from django.db import IntegrityError
from django.test import TestCase
from django.utils import timezone

from core.models.elo import EloRating
from core.models.enums import SeasonType
from core.models.match import Match
from core.models.team import Team


class EloRatingModelTests(TestCase):
    """Behavior tests for :class:`EloRating`."""

    def _create_team(self, school: str = "Test Team") -> Team:
        """Create a minimal team for use in Elo rating tests."""
        return Team.objects.create(
            school=school,
            color="#ffffff",
            alternate_color="#000000",
        )

    def _create_match(self, home: Team, away: Team) -> Match:
        """Create a minimal match between two teams."""
        return Match.objects.create(
            season=2024,
            week=1,
            season_type=SeasonType.REGULAR,
            start_date=timezone.now(),
            home_team=home,
            away_team=away,
        )

    def test_str_includes_identifiers(self) -> None:
        """``__str__`` should include season-week, team and rating."""
        home = self._create_team("String Home")
        away = self._create_team("String Away")
        match = self._create_match(home, away)
        rating = EloRating.objects.create(
            team=home,
            match=match,
            rating_before=1500,
            rating_after=1520,
        )
        self.assertEqual(str(rating), "2024-1 String Home: 1520")

    def test_rating_change_generated_field(self) -> None:
        """``rating_change`` reflects ``rating_after - rating_before``."""
        home = self._create_team("Change Home")
        away = self._create_team("Change Away")
        match = self._create_match(home, away)
        rating = EloRating.objects.create(
            team=home,
            match=match,
            rating_before=1500,
            rating_after=1550,
        )
        rating.refresh_from_db()
        self.assertEqual(rating.rating_change, 50.0)

    def test_unique_team_match_constraint(self) -> None:
        """Cannot create duplicate ratings for the same team and match."""
        home = self._create_team("Dup Home")
        away = self._create_team("Dup Away")
        match = self._create_match(home, away)
        EloRating.objects.create(
            team=home,
            match=match,
            rating_before=1500,
            rating_after=1510,
        )
        with self.assertRaises(IntegrityError):
            EloRating.objects.create(
                team=home,
                match=match,
                rating_before=1510,
                rating_after=1520,
            )
