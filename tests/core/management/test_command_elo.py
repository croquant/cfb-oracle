"""Tests for the elo management command."""

import io
from importlib import import_module

from django.test import TestCase
from django.utils import timezone

from core.models.elo import EloRating
from core.models.enums import SeasonType
from core.models.match import Match
from core.models.team import Team
from libs.constants import (
    ELO_DEFAULT_RATING,
    ELO_HOME_ADVANTAGE,
    ELO_K_FACTOR,
)

elo_module = import_module("core.management.commands.elo")
Command = elo_module.Command
_expected_score = elo_module._expected_score


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
        neutral_site: bool = False,
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
            neutral_site=neutral_site,
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
        self.assertAlmostEqual(a_ratings[0].rating_before, ELO_DEFAULT_RATING)

        expected_a_home = _expected_score(
            ELO_DEFAULT_RATING + ELO_HOME_ADVANTAGE, ELO_DEFAULT_RATING
        )
        a_after1 = ELO_DEFAULT_RATING + ELO_K_FACTOR * (1 - expected_a_home)
        b_after1 = ELO_DEFAULT_RATING + ELO_K_FACTOR * (
            0 - (1 - expected_a_home)
        )

        expected_b_home = _expected_score(
            b_after1 + ELO_HOME_ADVANTAGE, a_after1
        )
        b_after2 = b_after1 + ELO_K_FACTOR * (1 - expected_b_home)
        a_after2 = a_after1 + ELO_K_FACTOR * (0 - (1 - expected_b_home))

        self.assertAlmostEqual(a_ratings[0].rating_after, a_after1, places=2)
        self.assertAlmostEqual(a_ratings[1].rating_before, a_after1, places=2)
        self.assertAlmostEqual(a_ratings[1].rating_after, a_after2, places=2)

        output = self.command.stdout.getvalue()
        self.assertIn(
            (
                f"A: {ELO_DEFAULT_RATING:.2f} -> {a_after1:.2f}, "
                f"B: {ELO_DEFAULT_RATING:.2f} -> {b_after1:.2f}"
            ),
            output,
        )
        self.assertIn(
            (
                f"B: {b_after1:.2f} -> {b_after2:.2f}, "
                f"A: {a_after1:.2f} -> {a_after2:.2f}"
            ),
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
        expected_b_away = _expected_score(
            ELO_DEFAULT_RATING, ELO_DEFAULT_RATING + ELO_HOME_ADVANTAGE
        )
        b_after = ELO_DEFAULT_RATING + ELO_K_FACTOR * (1 - expected_b_away)
        self.assertAlmostEqual(b_ratings[0].rating_after, b_after, places=2)
        self.assertLess(b_ratings[1].rating_after, b_ratings[0].rating_after)

    def test_home_vs_away_advantage(self) -> None:
        """Away wins yield larger gains than home wins with equal ratings."""
        a = self._team("A")
        b = self._team("B")

        # A wins at home
        self._match(
            season=2024,
            week=1,
            home=a,
            away=b,
            home_score=20,
            away_score=10,
        )
        self.command.handle()
        home_gain = (
            EloRating.objects.get(team=a).rating_after - ELO_DEFAULT_RATING
        )

        Match.objects.all().delete()

        # A wins away
        self._match(
            season=2024,
            week=1,
            home=b,
            away=a,
            home_score=10,
            away_score=20,
        )
        # reinitialize command output
        self.command = Command()
        self.command.stdout = io.StringIO()
        self.command.stderr = io.StringIO()
        self.command.handle()
        away_gain = (
            EloRating.objects.get(team=a).rating_after - ELO_DEFAULT_RATING
        )

        self.assertGreater(away_gain, home_gain)

    def test_neutral_site_no_home_advantage(self) -> None:
        """Neutral site matches do not apply home-field advantage."""
        a = self._team("A")
        b = self._team("B")
        self._match(
            season=2024,
            week=1,
            home=a,
            away=b,
            home_score=20,
            away_score=10,
            neutral_site=True,
        )

        self.command.handle()

        self.assertEqual(EloRating.objects.count(), 2)
        home_rating = EloRating.objects.get(team=a)
        away_rating = EloRating.objects.get(team=b)
        expected = _expected_score(ELO_DEFAULT_RATING, ELO_DEFAULT_RATING)
        home_after = ELO_DEFAULT_RATING + ELO_K_FACTOR * (1 - expected)
        away_after = ELO_DEFAULT_RATING + ELO_K_FACTOR * (0 - (1 - expected))

        self.assertAlmostEqual(home_rating.rating_after, home_after, places=2)
        self.assertAlmostEqual(away_rating.rating_after, away_after, places=2)
