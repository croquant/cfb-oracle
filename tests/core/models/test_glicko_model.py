"""Tests for the :class:`GlickoRating` model."""

from django.test import TestCase

from core.models.enums import DivisionClassification
from core.models.glicko import GlickoRating
from core.models.team import Team


class GlickoRatingModelTests(TestCase):
    """Behavior tests for :class:`GlickoRating`."""

    def _create_team(self, school: str = "Test Team") -> Team:
        """Create a minimal team for use in Glicko rating tests."""
        return Team.objects.create(
            school=school,
            color="#ffffff",
            alternate_color="#000000",
        )

    def test_str_includes_identifiers(self) -> None:
        """``__str__`` should include season-week, team and rating."""
        team = self._create_team("String Team")
        rating = GlickoRating.objects.create(
            team=team,
            season=2024,
            week=3,
            classification=DivisionClassification.FBS,
            rating=1600,
            rd=30,
            vol=0.12,
        )
        self.assertEqual(str(rating), "2024-3 String Team: 1600")

    def test_rating_change_generated_field(self) -> None:
        """``rating_change`` reflects ``rating - previous_rating``."""
        team = self._create_team("Change Team")
        rating = GlickoRating.objects.create(
            team=team,
            season=2024,
            week=1,
            rating=1550,
            rd=40,
            vol=0.12,
            previous_rating=1500,
            previous_rd=350,
            previous_vol=0.11,
        )
        rating.refresh_from_db()
        self.assertEqual(rating.rating_change, 50.0)
