from typing import List

from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext

from core.models.team import Team, TeamAlternativeName, TeamLogo


class TeamManagerTests(TestCase):
    def _create_team(
        self,
        school: str,
        logos: List[str],
        alt_names: List[str],
        mascot: str | None = None,
    ):
        """Helper to create a team with optional related objects."""
        team = Team.objects.create(
            school=school,
            color="#ffffff",
            alternate_color="#000000",
            mascot=mascot,
        )
        for url in logos:
            TeamLogo.objects.create(team=team, url=url)
        for name in alt_names:
            TeamAlternativeName.objects.create(team=team, name=name)
        return team

    def test_prefetch_related(self):
        """The default manager should prefetch logos and alt names."""
        for idx in range(3):
            # Each team gets two logos and one alternative name
            self._create_team(
                f"Tech {idx}", [f"url{idx}a", f"url{idx}b"], [f"Alt {idx}"]
            )

        # Accessing related fields should not incur extra queries
        with CaptureQueriesContext(connection) as ctx:
            teams = list(Team.objects.filter(school__icontains="Tech"))
            for team in teams:
                team.logo_bright
                team.logo_dark
                list(team.alternative_names.all())

        # One query for teams, one for logos, and one for alt names
        self.assertEqual(len(ctx.captured_queries), 3)

    def test_logo_bright(self):
        """``logo_bright`` returns the first logo URL."""
        team = self._create_team("Bright Team", ["url1", "url2"], [])
        self.assertEqual(team.logo_bright, "url1")

    def test_logo_bright_none(self):
        """``logo_bright`` is ``None`` when no logos exist."""
        team = self._create_team("No Logo Team", [], [])
        self.assertIsNone(team.logo_bright)

    def test_logo_dark(self):
        """``logo_dark`` returns the second logo URL."""
        team = self._create_team("Dark Team", ["url1", "url2", "url3"], [])
        self.assertEqual(team.logo_dark, "url2")

    def test_logo_dark_none(self):
        """``logo_dark`` is ``None`` when fewer than two logos exist."""
        team = self._create_team("Single Logo Team", ["url1"], [])
        self.assertIsNone(team.logo_dark)

    def test_with_related_manager_prefetches(self):
        """Calling ``with_related`` should prefetch related models."""
        for idx in range(3):
            self._create_team(
                f"With Related {idx}",
                [f"url{idx}a", f"url{idx}b"],
                [f"Alt {idx}"],
            )

        # Using the explicit manager method should keep query count constant
        with CaptureQueriesContext(connection) as ctx:
            teams = list(
                Team.objects.with_related().filter(school__icontains="With Related")
            )
            for team in teams:
                team.logo_bright
                team.logo_dark
                list(team.alternative_names.all())

        self.assertEqual(len(ctx.captured_queries), 3)

    def test_team_str_with_mascot(self):
        """``__str__`` should include the mascot when present."""
        team = self._create_team(
            "Georgia", [], [], mascot="Bulldogs"
        )
        self.assertEqual(str(team), "Georgia Bulldogs")

    def test_team_str_without_mascot(self):
        """``__str__`` without a mascot returns just the school name."""
        team = self._create_team("Georgia Tech", [], [])
        self.assertEqual(str(team), "Georgia Tech")

    def test_save_generates_unique_slugs(self):
        """Saving teams with the same school should increment slug suffix."""
        t1 = self._create_team("Slug School", [], [])
        t2 = self._create_team("Slug School", [], [])
        t3 = self._create_team("Slug School", [], [])

        self.assertEqual(t1.slug, "slug-school")
        self.assertEqual(t2.slug, "slug-school-1")
        self.assertEqual(t3.slug, "slug-school-2")

    def test_save_preserves_existing_slug(self):
        """Saving again shouldn't alter a valid, unique slug."""
        team = self._create_team("Persistent Slug", [], [])

        # Slug is generated on initial save; calling save again should leave it
        # untouched because it already matches the slugified school name.
        original = team.slug
        team.save()
        self.assertEqual(team.slug, original)

    def test_team_alternative_name_str(self):
        """``TeamAlternativeName.__str__`` returns '<name> (<school>)'."""
        team = self._create_team("Name Team", [], ["Nickname"])
        alt = team.alternative_names.first()
        self.assertEqual(str(alt), "Nickname (Name Team)")

    def test_team_logo_str(self):
        """``TeamLogo.__str__`` includes the team school and URL."""
        team = self._create_team("Logo Team", ["http://logo"], [])
        logo = team.logos.first()
        self.assertEqual(str(logo), f"Logo for {team.school}: http://logo")
