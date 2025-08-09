from datetime import datetime, timezone as dt_timezone

from django.db import IntegrityError, transaction
from django.test import TestCase

from core.models.enums import SeasonType
from core.models.match import Match
from core.models.team import Team


class MatchModelTests(TestCase):
    def setUp(self):
        self.home_team = Team.objects.create(
            school="Home Team",
            color="#ffffff",
            alternate_color="#000000",
        )
        self.away_team = Team.objects.create(
            school="Away Team",
            color="#ffffff",
            alternate_color="#000000",
        )
        self.start = datetime(2023, 1, 1, 12, 0, tzinfo=dt_timezone.utc)

    def test_incomplete_match_without_scores(self):
        """An incomplete match may omit scores."""
        match = Match.objects.create(
            season=2023,
            week=1,
            season_type=SeasonType.REGULAR,
            start_date=self.start,
            completed=False,
            home_team=self.home_team,
            away_team=self.away_team,
        )
        self.assertIsNone(match.home_score)
        self.assertIsNone(match.away_score)

    def test_completed_match_requires_scores(self):
        """Completed matches must include scores."""
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Match.objects.create(
                    season=2023,
                    week=1,
                    season_type=SeasonType.REGULAR,
                    start_date=self.start,
                    completed=True,
                    home_team=self.home_team,
                    away_team=self.away_team,
                    home_score=21,
                )

    def test_str_returns_matchup_and_date(self):
        """``__str__`` returns the matchup and start date."""
        match = Match.objects.create(
            season=2023,
            week=2,
            season_type=SeasonType.REGULAR,
            start_date=self.start,
            completed=True,
            home_team=self.home_team,
            away_team=self.away_team,
            home_score=21,
            away_score=17,
        )
        self.assertEqual(
            str(match),
            f"{self.home_team} vs {self.away_team} on {self.start}",
        )
