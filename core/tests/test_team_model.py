from typing import List

from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext

from core.models.team import Team, TeamAlternativeName, TeamLogo


class TeamManagerTests(TestCase):
    def _create_team(self, school: str, logos: List[str], alt_names: List[str]):
        team = Team.objects.create(
            school=school,
            color="#ffffff",
            alternate_color="#000000",
        )
        for url in logos:
            TeamLogo.objects.create(team=team, url=url)
        for name in alt_names:
            TeamAlternativeName.objects.create(team=team, name=name)
        return team

    def test_prefetch_related(self):
        for idx in range(3):
            self._create_team(
                f"Tech {idx}", [f"url{idx}a", f"url{idx}b"], [f"Alt {idx}"]
            )

        with CaptureQueriesContext(connection) as ctx:
            teams = list(Team.objects.filter(school__icontains="Tech"))
            for team in teams:
                team.logo_bright
                team.logo_dark
                list(team.alternative_names.all())

        self.assertEqual(len(ctx.captured_queries), 3)

    def test_logo_bright(self):
        team = self._create_team("Bright Team", ["url1", "url2"], [])
        self.assertEqual(team.logo_bright, "url1")

    def test_logo_bright_none(self):
        team = self._create_team("No Logo Team", [], [])
        self.assertIsNone(team.logo_bright)

    def test_logo_dark(self):
        team = self._create_team("Dark Team", ["url1", "url2", "url3"], [])
        self.assertEqual(team.logo_dark, "url2")

    def test_logo_dark_none(self):
        team = self._create_team("Single Logo Team", ["url1"], [])
        self.assertIsNone(team.logo_dark)
