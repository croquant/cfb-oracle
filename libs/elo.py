"""Elo rating helpers."""

import math

from .constants import (
    ELO_HOME_ADVANTAGE,
    ELO_K_FACTOR,
    ELO_SCORE_DIFFERENTIAL_BASE,
)


def expected_score(rating_a: float, rating_b: float) -> float:
    """Return the expected score for ``rating_a`` against ``rating_b``."""
    return 1 / (1 + 10 ** ((rating_b - rating_a) / 400))


def update_ratings(
    home_rating: float,
    away_rating: float,
    home_score: int,
    away_score: int,
    *,
    k_factor: float = ELO_K_FACTOR,
    base: float = ELO_SCORE_DIFFERENTIAL_BASE,
    home_advantage: float = ELO_HOME_ADVANTAGE,
    neutral_site: bool = False,
) -> tuple[float, float]:
    """
    Update and return the Elo ratings for a completed match.

    ``home_rating`` and ``away_rating`` are the pre-match ratings.
    ``home_score`` and ``away_score`` are the final scores.

    The ``k_factor`` controls rating volatility. ``base`` adjusts how score
    differential scales the rating change. ``home_advantage`` is added to the
    home team's rating when the game is not at a neutral site.
    """
    if home_score > away_score:
        home_actual, away_actual = 1.0, 0.0
    elif home_score < away_score:
        home_actual, away_actual = 0.0, 1.0
    else:
        home_actual = away_actual = 0.5

    advantage = 0 if neutral_site else home_advantage
    expected_home = expected_score(home_rating + advantage, away_rating)
    expected_away = 1 - expected_home

    score_diff = abs(home_score - away_score)
    margin = math.log(score_diff + 1, base)

    home_after = home_rating + k_factor * margin * (home_actual - expected_home)
    away_after = away_rating + k_factor * margin * (away_actual - expected_away)

    return home_after, away_after
