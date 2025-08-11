"""Tests for team-related views."""

from django.test import TestCase
from django.urls import reverse

from core.models.enums import DivisionClassification
from core.models.glicko import GlickoRating
from core.models.team import Team


class TeamDetailViewTests(TestCase):
    """Tests for the TeamDetailView and related links."""

    def setUp(self) -> None:
        """Create a team and rating for view tests."""
        self.team = Team.objects.create(
            school="Team A",
            color="#000000",
            alternate_color="#FFFFFF",
            classification=DivisionClassification.FBS,
        )
        GlickoRating.objects.create(
            team=self.team,
            season=2024,
            week=1,
            classification=DivisionClassification.FBS,
            rating=1500,
            rd=30,
            vol=0.06,
        )
        self.ranking_url = reverse(
            "rankings", args=[DivisionClassification.FBS]
        )

    def test_team_detail_view_renders(self) -> None:
        """The detail view should render with the team context."""
        url = self.team.get_absolute_url()
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "team_detail.html")
        self.assertEqual(response.context["team"], self.team)

    def test_link_from_ranking_table_resolves(self) -> None:
        """Team links in ranking table should resolve to the detail view."""
        response = self.client.get(self.ranking_url)
        detail_url = self.team.get_absolute_url()
        self.assertContains(response, f'href="{detail_url}"')
        link_response = self.client.get(detail_url)
        self.assertEqual(link_response.status_code, 200)
        self.assertTemplateUsed(link_response, "team_detail.html")
