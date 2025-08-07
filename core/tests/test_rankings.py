from django.test import TestCase
from django.urls import reverse

from core.models.enums import DivisionClassification
from core.models.glicko import GlickoRating
from core.models.team import Team
from libs.constants import DEFAULT_RD, DEFAULT_VOLATILITY


class RankingViewTests(TestCase):
    def setUp(self):
        self.season = 2023
        self.week = 1
        self.teams = {}
        for classification in DivisionClassification.values:
            team = Team.objects.create(
                school=f"School {classification}",
                classification=classification,
                color="#fff",
                alternate_color="#000",
            )
            GlickoRating.objects.create(
                team=team,
                season=self.season,
                week=self.week,
                rating=1500,
                rd=DEFAULT_RD,
                vol=DEFAULT_VOLATILITY,
            )
            self.teams[classification] = team

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
