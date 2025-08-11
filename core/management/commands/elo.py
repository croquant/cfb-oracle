"""Management command to calculate Elo ratings for matches."""

import math

from django.core.management.base import BaseCommand

from core.models.elo import EloRating
from core.models.match import Match
from libs.constants import (
    ELO_DEFAULT_RATING,
    ELO_HOME_ADVANTAGE,
    ELO_K_FACTOR,
    ELO_SCORE_DIFFERENTIAL_BASE,
)


def _expected_score(rating_a: float, rating_b: float) -> float:
    """Return expected score for ``rating_a`` against ``rating_b``."""
    return 1 / (1 + 10 ** ((rating_b - rating_a) / 400))


class Command(BaseCommand):
    """Calculate Elo ratings for each team in each match."""

    help = "Calculate Elo ratings for each team in each match"

    k_factor = ELO_K_FACTOR

    def handle(self, *args: str, **options: int | str | None) -> None:  # noqa: D401
        """Run the Elo rating calculation."""
        self.stdout.write("Clearing existing Elo ratings...")
        EloRating.objects.all().delete()

        self.stdout.write("Calculating Elo ratings...")
        current_ratings: dict[int, float] = {}
        rating_records: list[EloRating] = []

        matches = Match.objects.filter(completed=True).order_by(
            "season", "week", "start_date", "id"
        )

        for match in matches:
            home_before = current_ratings.get(
                match.home_team_id, ELO_DEFAULT_RATING
            )
            away_before = current_ratings.get(
                match.away_team_id, ELO_DEFAULT_RATING
            )

            if (
                match.home_score is None or match.away_score is None
            ):  # pragma: no cover
                # skip matches without scores
                continue

            if match.home_score > match.away_score:
                home_actual, away_actual = 1.0, 0.0
            elif match.home_score < match.away_score:
                home_actual, away_actual = 0.0, 1.0
            else:
                home_actual = away_actual = 0.5

            advantage = 0 if match.neutral_site else ELO_HOME_ADVANTAGE
            expected_home = _expected_score(
                home_before + advantage, away_before
            )
            expected_away = 1 - expected_home

            score_diff = abs(match.home_score - match.away_score)
            # Rating change formula with score differential scaling:
            # rating_after = rating_before + K * log(diff + 1, BASE)
            #                 * (actual - expected)
            margin = math.log(score_diff + 1, ELO_SCORE_DIFFERENTIAL_BASE)
            home_after = home_before + self.k_factor * margin * (
                home_actual - expected_home
            )
            away_after = away_before + self.k_factor * margin * (
                away_actual - expected_away
            )

            self.stdout.write(
                f"{match.home_team.school}: "
                f"{home_before:.2f} -> {home_after:.2f}, "
                f"{match.away_team.school}: {away_before:.2f} -> "
                f"{away_after:.2f}"
            )

            rating_records.append(
                EloRating(
                    team_id=match.home_team_id,
                    match_id=match.id,
                    rating_before=home_before,
                    rating_after=home_after,
                )
            )
            rating_records.append(
                EloRating(
                    team_id=match.away_team_id,
                    match_id=match.id,
                    rating_before=away_before,
                    rating_after=away_after,
                )
            )

            current_ratings[match.home_team_id] = home_after
            current_ratings[match.away_team_id] = away_after

        if rating_records:
            EloRating.objects.bulk_create(rating_records, batch_size=500)
