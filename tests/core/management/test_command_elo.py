"""Tests for the elo management command."""

import io
from importlib import import_module

from django.test import TestCase
from django.utils import timezone

from core.models.elo import EloRating
from core.models.enums import SeasonType
from core.models.match import Match
from core.models.team import Team

Command = import_module("core.management.commands.elo").Command


class EloCommandTests(TestCase):
    """Behavior tests for the elo rating command."""

    def setUp(self) -> None:
        """Create a command instance with captured output."""
        self.command = Command()
        self.command.stdout = io.StringIO()
        self.command.stderr = io.StringIO()

    def _team(self, name: str) -> Team:
        return Team.objects.create(
            school=name,
            color="#fff",
            alternate_color="#000",
        )

    def _match(
        self,
        *,
        season: int,
        week: int,
        home: Team,
        away: Team,
        home_score: int,
        away_score: int,
    ) -> Match:
        return Match.objects.create(
            season=season,
            week=week,
            season_type=SeasonType.REGULAR,
            start_date=timezone.now(),
            completed=True,
            home_team=home,
            away_team=away,
            home_score=home_score,
            away_score=away_score,
        )

    # handle ---------------------------------------------------------------
    def test_handle_no_matches(self) -> None:
        """Running ``handle`` with no data creates no ratings."""
        self.command.handle()
        self.assertEqual(EloRating.objects.count(), 0)

    def test_handle_creates_ratings_per_match(self) -> None:
        """``handle`` creates ratings and carries them across matches."""
        a = self._team("A")
        b = self._team("B")
        self._match(
            season=2024,
            week=1,
            home=a,
            away=b,
            home_score=20,
            away_score=10,
        )
        self._match(
            season=2024,
            week=2,
            home=b,
            away=a,
            home_score=30,
            away_score=10,
        )

        self.command.handle()

        self.assertEqual(EloRating.objects.count(), 4)

        a_ratings = list(
            EloRating.objects.filter(team=a).order_by("match__week")
        )
        self.assertAlmostEqual(a_ratings[0].rating_before, 1500)
        self.assertAlmostEqual(a_ratings[0].rating_after, 1516, places=2)
        self.assertAlmostEqual(a_ratings[1].rating_before, 1516, places=2)
        self.assertAlmostEqual(a_ratings[1].rating_after, 1498.53, places=2)

        output = self.command.stdout.getvalue()
        self.assertIn(
            "A: 1500.00 -> 1516.00, B: 1500.00 -> 1484.00",
            output,
        )
        self.assertIn(
            "B: 1484.00 -> 1501.47, A: 1516.00 -> 1498.53",
            output,
        )

    def test_handle_away_win_and_tie(self) -> None:
        """Away wins and ties are reflected in rating changes."""
        a = self._team("A")
        b = self._team("B")
        # away team wins
        self._match(
            season=2024,
            week=1,
            home=a,
            away=b,
            home_score=10,
            away_score=20,
        )
        # tie match
        self._match(
            season=2024,
            week=2,
            home=b,
            away=a,
            home_score=14,
            away_score=14,
        )

        self.command.handle()

        self.assertEqual(EloRating.objects.count(), 4)
        b_ratings = list(
            EloRating.objects.filter(team=b).order_by("match__week")
        )
        self.assertAlmostEqual(b_ratings[0].rating_after, 1516, places=2)
        self.assertLess(b_ratings[1].rating_after, b_ratings[0].rating_after)
