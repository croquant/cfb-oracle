import os
import math
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.test import TestCase
from libs.glicko2 import Player
from libs.constants import GLICKO2_SCALER


class Glicko2Test(TestCase):
    def setUp(self):
        """Create a baseline player and deterministic match data."""

        self.player = Player(rating=1500, rd=200, vol=0.06, tau=0.5)

        # Opponent ratings, deviations, and outcomes from example matches
        self.rating_list = [1400, 1550, 1700]
        self.rd_list = [30, 100, 300]
        self.outcome_list = [1, 0, 0]

        # Pre-scale inputs for internal Glicko-2 calculations
        self.scaled_ratings = [
            (x - 1500) / GLICKO2_SCALER for x in self.rating_list
        ]
        self.scaled_rds = [x / GLICKO2_SCALER for x in self.rd_list]

    def test_pre_rating_rd(self):
        """``_pre_rating_rd`` increases the rating deviation via volatility."""

        p = Player(rating=1500, rd=200, vol=0.06, tau=0.5)
        p._pre_rating_rd()

        # RD grows by volatility before being rescaled
        expected_rd = math.sqrt((200 / GLICKO2_SCALER) ** 2 + 0.06**2) * GLICKO2_SCALER
        self.assertAlmostEqual(p.rd, expected_rd, places=12)

    def test_new_vol(self):
        """``_new_vol`` returns the expected post-match volatility."""

        v = self.player._v(self.scaled_ratings, self.scaled_rds)
        new_vol = self.player._new_vol(
            self.scaled_ratings, self.scaled_rds, self.outcome_list, v
        )

        # Volatility converges to a known value for this match history
        self.assertAlmostEqual(new_vol, 0.05999342315486217)

    def test_new_vol_if_branch(self):
        """``_new_vol`` handles large ``delta`` using the logarithmic case."""

        p = Player(rating=1500, rd=30, vol=0.06, tau=0.5)
        rating_list = [500]
        rd_list = [30]
        outcome_list = [0]

        # Scale inputs for the internal Glicko-2 representation
        scaled_ratings = [(x - 1500) / GLICKO2_SCALER for x in rating_list]
        scaled_rds = [x / GLICKO2_SCALER for x in rd_list]
        v = p._v(scaled_ratings, scaled_rds)

        # With a massive upset loss, ``delta`` is large enough to trigger
        # the ``delta**2 > rd**2 + v`` branch in step 2.
        self.assertAlmostEqual(
            p._new_vol(scaled_ratings, scaled_rds, outcome_list, v),
            0.06001325617796023,
        )

    def test_new_vol_expands_bounds(self):
        """``_new_vol`` expands the search interval when ``f`` is negative."""

        class LoopPlayer(Player):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self._first = True

            def _f(self, x, delta, v, a):
                if self._first:
                    # Force the initial check negative so the loop executes
                    self._first = False
                    return -abs(super()._f(x, delta, v, a)) - 1
                return super()._f(x, delta, v, a)

        p = LoopPlayer(rating=1500, rd=200, vol=0.06, tau=0.5)
        v = p._v(self.scaled_ratings, self.scaled_rds)
        new_vol = p._new_vol(self.scaled_ratings, self.scaled_rds, self.outcome_list, v)

        # Forcing the loop still converges to the known post-match volatility.
        self.assertAlmostEqual(new_vol, 0.05999342315486217, places=9)

    def test_update_player(self):
        """``update_player`` applies rating, RD, and volatility updates."""

        self.player.update_player(
            self.rating_list, self.rd_list, self.outcome_list
        )

        # Updated values match the example from the Glicko-2 paper
        self.assertAlmostEqual(self.player.rating, 1464.0506752970196)
        self.assertAlmostEqual(self.player.rd, 151.51651409762084)
        self.assertAlmostEqual(self.player.vol, 0.05999342315486217)

    def test_did_not_compete(self):
        """``did_not_compete`` defers updates but increases the RD."""

        p = Player(rating=1500, rd=50, vol=0.06, tau=0.5)
        p.did_not_compete()

        # Rating deviation grows identically to ``_pre_rating_rd``.
        expected_rd = math.sqrt((50 / GLICKO2_SCALER) ** 2 + 0.06**2) * GLICKO2_SCALER
        self.assertAlmostEqual(p.rd, expected_rd, places=12)
