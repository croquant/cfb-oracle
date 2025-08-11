"""Management command to calculate Elo ratings for matches."""

import argparse

from django.core.management.base import BaseCommand, CommandError

from core.models.elo import EloRating
from core.models.match import Match
from libs.constants import ELO_DEFAULT_RATING, ELO_K_FACTOR
from libs.elo import update_ratings


class Command(BaseCommand):
    """Calculate Elo ratings for each team in each match."""

    help = "Calculate Elo ratings for each team in each match"

    k_factor = ELO_K_FACTOR

    def add_arguments(self, parser: argparse.ArgumentParser) -> None:  # noqa: D401
        """Add command arguments."""
        parser.add_argument(
            "--decay",
            type=float,
            default=0.5,
            help=(
                "Fraction of a team's rating carried over between seasons "
                "(0 for full reset, 1 for no decay)."
            ),
        )

    def handle(self, *args: str, **options: int | str | None) -> None:  # noqa: D401
        """Run the Elo rating calculation."""
        decay = float(options.get("decay", 0.5))
        if not 0 <= decay <= 1:
            raise CommandError("decay must be between 0 and 1")

        self.stdout.write("Clearing existing Elo ratings...")
        EloRating.objects.all().delete()

        self.stdout.write("Calculating Elo ratings...")
        current_ratings: dict[int, float] = {}
        rating_records: list[EloRating] = []

        matches = Match.objects.filter(completed=True).order_by(
            "season", "week", "start_date", "id"
        )

        current_season: int | None = None

        for match in matches:
            if current_season is None:
                current_season = match.season
            elif match.season != current_season:
                current_season = match.season
                for team_id, rating in current_ratings.items():
                    current_ratings[team_id] = (
                        ELO_DEFAULT_RATING
                        if decay == 0
                        else rating * decay + ELO_DEFAULT_RATING * (1 - decay)
                    )

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

            home_after, away_after = update_ratings(
                home_before,
                away_before,
                match.home_score,
                match.away_score,
                k_factor=self.k_factor,
                neutral_site=match.neutral_site,
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
