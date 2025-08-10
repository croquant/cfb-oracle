"""Tests for ranking views."""

from django.core.cache import cache
from django.test import RequestFactory, TestCase
from django.urls import reverse

from core.models.enums import DivisionClassification
from core.models.glicko import GlickoRating
from core.models.team import Team
from core.views.ranking_views import RankingListView


class RankingListViewTests(TestCase):
    """Ranking list view tests with data."""

    def setUp(self) -> None:
        """Create teams and rating data for tests."""
        cache.clear()
        self.factory = RequestFactory()
        self.team1 = Team.objects.create(
            school="Team A",
            color="#000000",
            alternate_color="#FFFFFF",
            classification=DivisionClassification.FBS,
        )
        self.team2 = Team.objects.create(
            school="Team B",
            color="#111111",
            alternate_color="#EEEEEE",
            classification=DivisionClassification.FBS,
        )
        GlickoRating.objects.create(
            team=self.team1,
            season=2023,
            week=1,
            classification=DivisionClassification.FBS,
            rating=1500,
            rd=30,
            vol=0.06,
        )
        GlickoRating.objects.create(
            team=self.team2,
            season=2023,
            week=2,
            classification=DivisionClassification.FBS,
            rating=1400,
            rd=30,
            vol=0.06,
        )
        GlickoRating.objects.create(
            team=self.team1,
            season=2024,
            week=1,
            classification=DivisionClassification.FBS,
            rating=1550,
            rd=30,
            vol=0.06,
        )
        self.url = reverse("rankings", args=[DivisionClassification.FBS])

    def test_standard_template_and_context(self) -> None:
        """Standard request should render the full template and context."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "ranking.html")
        self.assertEqual(response.context["season"], 2024)
        self.assertEqual(response.context["week"], 1)
        self.assertEqual(response.context["seasons"], [2023, 2024])
        self.assertEqual(response.context["weeks"], [1])
        self.assertEqual(
            response.context["classification"], DivisionClassification.FBS
        )
        self.assertEqual(response.context["classification_label"], "FBS")
        self.assertEqual(response.context["title"], "FBS Rankings")
        ratings = list(response.context["ratings"])
        self.assertEqual(len(ratings), 1)
        self.assertEqual(ratings[0].rating, 1550)

    def test_htmx_template(self) -> None:
        """HTMX request should render the partial template."""
        response = self.client.get(self.url, HTTP_HX_REQUEST="true")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "cotton/ranking_table.html")

    def test_cache_hit_for_seasons_and_weeks(self) -> None:
        """Second request should hit the cache and log debug messages."""
        self.client.get(self.url)  # prime cache
        with self.assertLogs("core.views.ranking_views", level="DEBUG") as log:
            self.client.get(self.url)
        self.assertIn("Cache hit for seasons", log.output[0])
        self.assertIn("Cache hit for weeks", log.output[1])

    def test_get_season_and_week_with_params(self) -> None:
        """Valid query params should select the requested season and week."""
        response = self.client.get(f"{self.url}?season=2023&week=2")
        self.assertEqual(response.context["season"], 2023)
        self.assertEqual(response.context["week"], 2)
        self.assertEqual(response.context["weeks"], [1, 2])
        ratings = list(response.context["ratings"])
        self.assertEqual(len(ratings), 1)
        self.assertEqual(ratings[0].season, 2023)
        self.assertEqual(ratings[0].week, 2)

    def test_invalid_query_defaults_to_latest(self) -> None:
        """Invalid query params should fall back to latest season and week."""
        response = self.client.get(f"{self.url}?season=9999&week=abc")
        self.assertEqual(response.context["season"], 2024)
        self.assertEqual(response.context["week"], 1)

    def test_invalid_classification_raises_404(self) -> None:
        """An invalid classification should raise 404."""
        response = self.client.get(reverse("rankings", args=["bad"]))
        self.assertEqual(response.status_code, 404)


class RankingListViewNoDataTests(TestCase):
    """Ranking list view tests without existing data."""

    def setUp(self) -> None:
        """Clear cache for each test."""
        cache.clear()
        self.factory = RequestFactory()

    def test_get_queryset_and_context_no_data(self) -> None:
        """Without data the view should return empty context values."""
        view = RankingListView()
        request = self.factory.get("/rankings/")
        view.request = request
        view.kwargs = {}
        qs = view.get_queryset()
        self.assertEqual(list(qs), [])
        self.assertIsNone(view.season)
        self.assertIsNone(view.week)
        context = view.get_context_data(object_list=qs)
        self.assertEqual(context["seasons"], [])
        self.assertIsNone(context["season"])
        self.assertEqual(context["weeks"], [])
        self.assertIsNone(context["week"])
        self.assertIsNone(context["classification"])
        self.assertIsNone(context["classification_label"])
        self.assertEqual(context["title"], "Rankings")

    def test_get_season_and_week_no_data(self) -> None:
        """Return empty season and week lists when no data exists."""
        view = RankingListView()
        request = self.factory.get("/rankings/")
        view.request = request
        view.kwargs = {}
        season, week, seasons, weeks = view.get_season_and_week(
            GlickoRating.objects.none()
        )
        self.assertIsNone(season)
        self.assertIsNone(week)
        self.assertEqual(seasons, [])
        self.assertEqual(weeks, [])
