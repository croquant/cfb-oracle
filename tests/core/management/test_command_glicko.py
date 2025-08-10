"""Tests for the glicko management command."""

import io
from importlib import import_module

from django.test import TestCase
from django.utils import timezone

from core.models.enums import DivisionClassification, SeasonType
from core.models.glicko import GlickoRating
from core.models.match import Match
from core.models.team import Team

Command = import_module("core.management.commands.glicko").Command


class GlickoCommandTests(TestCase):
    """Behavior tests for the glicko rating command."""

    def setUp(self) -> None:
        """Create a command instance with captured output."""
        self.command = Command()
        self.command.stdout = io.StringIO()
        self.command.stderr = io.StringIO()

    # helpers ---------------------------------------------------------------
    def _team(self, name: str) -> Team:
        return Team.objects.create(
            school=name,
            color="#fff",
            alternate_color="#000",
            classification=DivisionClassification.FBS,
        )

    # _get_player ----------------------------------------------------------
    def test_get_player_creates_and_reuses(self) -> None:
        """``_get_player`` creates a new player and reuses existing ones."""
        players: dict[int, object] = {}
        player = self.command._get_player(
            players, 1, DivisionClassification.FCS
        )
        self.assertEqual(player.rating, 1300)  # FCS base rating
        self.assertIs(players[1], player)
        again = self.command._get_player(players, 1, None)
        self.assertIs(player, again)

    # _process_season ------------------------------------------------------
    def test_process_season_no_matches(self) -> None:
        """Season with no matches returns an empty set and logs message."""
        players: dict[int, object] = {}
        active = self.command._process_season(2025, players)
        self.assertEqual(active, set())
        self.assertIn("No matches found", self.command.stdout.getvalue())

    # _calculate_* helpers -------------------------------------------------
    def test_calculate_bonus_and_cap(self) -> None:
        """Helper methods return expected bonus and cap values."""
        t1 = self._team("A")
        t2 = self._team("B")
        Match.objects.create(
            season=2023,
            week=1,
            season_type=SeasonType.REGULAR,
            start_date=timezone.now(),
            completed=True,
            neutral_site=False,
            home_team=t1,
            home_classification=DivisionClassification.FBS,
            away_team=t2,
            away_classification=DivisionClassification.FBS,
            home_score=20,
            away_score=10,
        )
        qs = Match.objects.filter(season=2023)
        bonus = self.command._calculate_home_field_bonus(qs, 1500)
        cap = self.command._calculate_margin_weight_cap(qs)
        self.assertEqual(bonus, 750)
        self.assertEqual(cap, 15)

    def test_calculate_bonus_and_cap_no_matches(self) -> None:
        """When no matches exist, bonus is 0 and cap defaults to 1.5."""
        qs = Match.objects.none()
        self.assertEqual(self.command._calculate_home_field_bonus(qs, 1500), 0)
        self.assertEqual(self.command._calculate_margin_weight_cap(qs), 1.5)

    # _update_ratings ------------------------------------------------------
    def test_update_ratings_empty(self) -> None:
        """No players results in no created ratings."""
        self.command._update_ratings(
            season=2024,
            week=1,
            players={},
            results={},
            margin_weight_cap=1.5,
            team_meta={},
            season_active_teams=set(),
        )
        self.assertEqual(GlickoRating.objects.count(), 0)

    # handle ---------------------------------------------------------------
    def test_handle_no_matches(self) -> None:
        """Running handle with no data should not create ratings."""
        self.command.handle()
        self.assertEqual(GlickoRating.objects.count(), 0)

    def test_handle_processes_matches_and_sets_active(self) -> None:
        """``handle`` processes matches and updates team activity."""
        a = self._team("A")
        b = self._team("B")
        c = self._team("C")
        d = self._team("D")
        now = timezone.now()
        Match.objects.create(
            season=2023,
            week=1,
            season_type=SeasonType.REGULAR,
            start_date=now,
            completed=True,
            neutral_site=False,
            home_team=a,
            home_classification=DivisionClassification.FBS,
            away_team=b,
            away_classification=DivisionClassification.FBS,
            home_score=30,
            away_score=20,
        )
        Match.objects.create(
            season=2024,
            week=1,
            season_type=SeasonType.REGULAR,
            start_date=now,
            completed=True,
            neutral_site=False,
            home_team=a,
            home_classification=DivisionClassification.FBS,
            away_team=c,
            away_classification=DivisionClassification.FBS,
            home_score=14,
            away_score=7,
        )
        Match.objects.create(
            season=2024,
            week=1,
            season_type=SeasonType.REGULAR,
            start_date=now,
            completed=True,
            neutral_site=True,
            home_team=c,
            home_classification=DivisionClassification.FBS,
            away_team=d,
            away_classification=DivisionClassification.FBS,
            home_score=3,
            away_score=10,
        )
        Match.objects.create(
            season=2024,
            week=1,
            season_type=SeasonType.REGULAR,
            start_date=now,
            completed=True,
            neutral_site=False,
            home_team=d,
            home_classification=DivisionClassification.FBS,
            away_team=a,
            away_classification=DivisionClassification.FBS,
            home_score=21,
            away_score=21,
        )

        self.command.handle()

        self.assertEqual(GlickoRating.objects.filter(season=2023).count(), 2)
        self.assertEqual(GlickoRating.objects.filter(season=2024).count(), 3)

        a.refresh_from_db()
        b.refresh_from_db()
        c.refresh_from_db()
        d.refresh_from_db()
        self.assertTrue(a.active)
        self.assertFalse(b.active)
        self.assertTrue(c.active)
        self.assertTrue(d.active)
