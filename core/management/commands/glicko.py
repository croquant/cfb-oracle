"""Management command to calculate Glicko ratings for each team."""

import math
from typing import Dict, List, Tuple

from django.core.management.base import BaseCommand
from django.db.models import Avg, F, QuerySet
from django.db.models.functions import Abs

from core.models.enums import DivisionClassification
from core.models.glicko import GlickoRating
from core.models.match import Match
from core.models.team import Team
from libs.constants import (
    DEFAULT_RATING,
    DEFAULT_RD,
    DIVISION_BASE_RATINGS,
    DIVISION_BASE_RDS,
)
from libs.glicko2 import Player


class Command(BaseCommand):
    """Calculate Glicko ratings for each team in each week."""

    help = "Calculate Glicko ratings for each team in each week"

    def handle(self, *args, **options):  # noqa: D401 - inherited from BaseCommand
        """Run the Glicko rating calculation."""
        self.stdout.write("Clearing existing ratings...")
        GlickoRating.objects.all().delete()

        self.stdout.write("Calculating Glicko ratings...")

        players: Dict[int, Player] = {}
        seasons = (
            Match.objects.order_by("season").values_list("season", flat=True).distinct()
        )

        for season in seasons:
            self._process_season(season, players)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _get_player(players: Dict[int, Player], team_id: int, division) -> Player:
        """Retrieve or create a :class:`Player` for the given team."""
        player = players.get(team_id)
        if player is None:
            rating = DIVISION_BASE_RATINGS.get(division, DEFAULT_RATING)
            rd = DIVISION_BASE_RDS.get(division, DEFAULT_RD)
            player = Player(rating=rating, rd=rd)
            players[team_id] = player
        return player

    def _process_season(self, season: int, players: Dict[int, Player]) -> None:
        """Process all matches for a single season."""
        matches_qs = Match.objects.filter(season=season, completed=True)
        if matches_qs.count() == 0:
            self.stdout.write(f"No matches found for season {season}. Skipping...")
            return

        prev_season = season - 1
        prev_matches_qs = Match.objects.filter(season=prev_season, completed=True)
        prev_season_avg_rating = GlickoRating.objects.filter(
            season=prev_season
        ).aggregate(avg_rating=Avg("rating"))["avg_rating"]

        home_field_bonus = self._calculate_home_field_bonus(
            prev_matches_qs, prev_season_avg_rating
        )
        margin_weight_cap = self._calculate_margin_weight_cap(prev_matches_qs)

        weeks = list(
            matches_qs.order_by("week").values_list("week", flat=True).distinct()
        )
        self.stdout.write(
            f"Processing season {season}... {matches_qs.count()} matches found across {len(weeks)} weeks."
        )

        season_active_teams: set[int] = set()
        for week in weeks:
            week_matches = matches_qs.filter(week=week).order_by("start_date")
            self.stdout.write(
                f"  Processing week {week}... {week_matches.count()} matches found."
            )
            self._process_week(
                season,
                week,
                week_matches,
                players,
                home_field_bonus,
                margin_weight_cap,
                season_active_teams,
            )

        if players:
            Team.objects.bulk_update(
                [
                    Team(id=team_id, active=(team_id in season_active_teams))
                    for team_id in players.keys()
                ],
                fields=["active"],
            )

    def _process_week(
        self,
        season: int,
        week: int,
        week_matches: QuerySet,
        players: Dict[int, Player],
        home_field_bonus: float,
        margin_weight_cap: float,
        season_active_teams: set[int],
    ) -> None:
        """Process all matches for a given week."""
        results: Dict[int, List[Tuple[float, float, float, float]]] = {}

        for match in week_matches:
            self._process_match(
                match,
                players,
                home_field_bonus,
                results,
                season_active_teams,
            )

        self._update_ratings(
            season, week, players, results, margin_weight_cap
        )

    def _process_match(
        self,
        match,
        players: Dict[int, Player],
        home_field_bonus: float,
        results: Dict[int, List[Tuple[float, float, float, float]]],
        season_active_teams: set[int],
    ) -> None:
        """Record the result of a single match."""
        home_division = (
            DivisionClassification(match.home_classification)
            if match.home_classification
            else None
        )
        home_team = self._get_player(players, match.home_team_id, home_division)

        away_division = (
            DivisionClassification(match.away_classification)
            if match.away_classification
            else None
        )
        away_team = self._get_player(players, match.away_team_id, away_division)

        season_active_teams.update([match.home_team_id, match.away_team_id])

        home_team_outcome = 0.5
        if match.home_score > match.away_score:
            home_team_outcome = 1
        elif match.home_score < match.away_score:
            home_team_outcome = 0
        away_team_outcome = 1 - home_team_outcome

        margin = abs(match.home_score - match.away_score)
        log_margin = math.log(margin + 1)

        if match.neutral_site:
            home_rating = home_team.rating
            away_rating = away_team.rating
        else:
            home_rating = home_team.rating + home_field_bonus / 2
            away_rating = away_team.rating - home_field_bonus / 2

        results.setdefault(match.home_team_id, []).append(
            (away_rating, away_team.rd, log_margin, home_team_outcome)
        )
        results.setdefault(match.away_team_id, []).append(
            (home_rating, home_team.rd, log_margin, away_team_outcome)
        )

    def _update_ratings(
        self,
        season: int,
        week: int,
        players: Dict[int, Player],
        results: Dict[int, List[Tuple[float, float, float, float]]],
        margin_weight_cap: float,
    ) -> None:
        """Update player ratings from match results."""
        ratings = []
        for player_id, player in players.items():
            before_rating = player.rating
            before_rd = player.rd
            before_vol = player.vol

            recs = results.get(player_id, [])
            if recs:
                r_list = [r for r, _, _, _ in recs]
                rd_list = [rd for _, rd, _, _ in recs]
                max_log_margin = math.log(margin_weight_cap + 1)
                o_list = [
                    0.5 + (o - 0.5) * min(lm, max_log_margin) / max_log_margin
                    for _, _, lm, o in recs
                ]
                player.update_player(r_list, rd_list, o_list)
            else:
                player.did_not_compete()

            ratings.append(
                GlickoRating(
                    team_id=player_id,
                    season=season,
                    week=week,
                    previous_rating=before_rating,
                    previous_rd=before_rd,
                    previous_vol=before_vol,
                    rating=player.rating,
                    rd=player.rd,
                    vol=player.vol,
                )
            )

        if ratings:
            GlickoRating.objects.bulk_create(
                ratings, batch_size=500, ignore_conflicts=True
            )

    @staticmethod
    def _calculate_home_field_bonus(
        prev_matches_qs: QuerySet, prev_season_avg_rating: float
    ) -> float:
        """Calculate the home field advantage bonus."""
        non_neutral_matches = prev_matches_qs.filter(neutral_site=False)
        total_non_neutral_matches = non_neutral_matches.count()
        if total_non_neutral_matches > 0:
            home_wins = non_neutral_matches.filter(
                home_score__gt=F("away_score")
            ).count()
            home_win_percent = home_wins / total_non_neutral_matches
            return (home_win_percent - 0.5) * prev_season_avg_rating
        return 0

    @staticmethod
    def _calculate_margin_weight_cap(prev_matches_qs: QuerySet) -> float:
        """Calculate the margin of victory weight cap."""
        prev_season_avg_margin = prev_matches_qs.aggregate(
            avg_margin=Avg(Abs(F("home_score") - F("away_score")))
        )["avg_margin"]
        return prev_season_avg_margin * 1.5 if prev_season_avg_margin else 1.5
