from django.test import TestCase
from django.urls import reverse

from core.models.enums import DivisionClassification
from core.models.glicko import GlickoRating
from core.models.team import Team
from libs.constants import DEFAULT_RD, DEFAULT_VOLATILITY
import json


class RankingViewTests(TestCase):
    def setUp(self):
        self.teams = {}
        for classification in DivisionClassification.values:
            team = Team.objects.create(
                school=f"School {classification}",
                classification=classification,
                color="#fff",
                alternate_color="#000",
            )
            self.teams[classification] = team

        # FBS has multiple seasons and weeks
        GlickoRating.objects.create(
            team=self.teams[DivisionClassification.FBS],
            season=2022,
            week=1,
            rating=1500,
            rd=DEFAULT_RD,
            vol=DEFAULT_VOLATILITY,
        )
        GlickoRating.objects.create(
            team=self.teams[DivisionClassification.FBS],
            season=2023,
            week=1,
            rating=1500,
            rd=DEFAULT_RD,
            vol=DEFAULT_VOLATILITY,
        )
        GlickoRating.objects.create(
            team=self.teams[DivisionClassification.FBS],
            season=2023,
            week=2,
            rating=1500,
            rd=DEFAULT_RD,
            vol=DEFAULT_VOLATILITY,
        )

        # Other classifications only have one season/week
        for classification in [
            DivisionClassification.FCS,
            DivisionClassification.II,
            DivisionClassification.III,
        ]:
            GlickoRating.objects.create(
                team=self.teams[classification],
                season=2023,
                week=1,
                rating=1500,
                rd=DEFAULT_RD,
                vol=DEFAULT_VOLATILITY,
            )

        self.season = 2023
        self.week = 1

    def test_rankings_filtered_by_classification(self):
        for classification in DivisionClassification.values:
            url = reverse("rankings", args=[classification])
            response = self.client.get(
                f"{url}?season={self.season}&week={self.week}"
            )
            ratings = list(response.context["ratings"])
            with self.subTest(classification=classification):
                self.assertEqual(len(ratings), 1)
                self.assertEqual(
                    ratings[0].team.classification, classification
                )

    def test_defaults_to_latest_season_and_week(self):
        url = reverse("rankings", args=[DivisionClassification.FBS])
        response = self.client.get(url)
        self.assertEqual(response.context["season"], 2023)
        self.assertEqual(response.context["week"], 2)

    def test_seasons_and_weeks_filtered_by_classification(self):
        url = reverse("rankings", args=[DivisionClassification.II])
        response = self.client.get(url)
        self.assertEqual(response.context["seasons"], [2023])
        weeks = json.loads(response.context["weeks_json"])
        self.assertEqual(weeks, {"2023": [1]})
