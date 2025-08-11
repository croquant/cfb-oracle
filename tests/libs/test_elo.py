"""Tests for Elo rating helpers."""

import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django
from django.test import TestCase

from libs.elo import expected_score, update_ratings

django.setup()


class EloHelpersTest(TestCase):
    """Tests for functions in :mod:`libs.elo`."""

    def test_expected_score(self) -> None:
        """``expected_score`` returns probabilities based on rating gap."""
        self.assertAlmostEqual(expected_score(1500, 1500), 0.5)
        self.assertAlmostEqual(expected_score(1600, 1500), 0.6400649998028851)

    def test_update_ratings_home_win(self) -> None:
        """Home team gains points after a home victory."""
        home_after, away_after = update_ratings(
            1500, 1500, 21, 14, neutral_site=False
        )
        self.assertAlmostEqual(home_after, 1512.1809715981456)
        self.assertAlmostEqual(away_after, 1487.8190284018544)

    def test_update_ratings_draw_no_change(self) -> None:
        """A draw does not adjust ratings when the margin is zero."""
        home_after, away_after = update_ratings(1500, 1500, 21, 21)
        self.assertEqual(home_after, 1500)
        self.assertEqual(away_after, 1500)
