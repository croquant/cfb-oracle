from django.core.management.base import BaseCommand

from core.models.glicko import GlickoRating
from core.models.match import Match
from core.models.team import Team
from libs.constants import MARGIN_WEIGHT_CAP
from libs.glicko2 import Player


class Command(BaseCommand):
    help = "Calculate Glicko ratings for each team in each season"

    def handle(self, *args, **options):
        # Clear existing ratings
        self.stdout.write("Clearing existing ratings...")
        GlickoRating.objects.all().delete()

        self.stdout.write("Calculating Glicko ratings...")
        players: dict[int, Player] = {}
        seasons = (
            Match.objects.order_by("season").values_list("season", flat=True).distinct()
        )
        for season in seasons:
            matches = (
                Match.objects.filter(season=season)
                .filter(completed=True)
                .order_by("start_date")
            )
            if not matches.exists():
                self.stdout.write(f"No matches found for season {season}. Skipping...")
                continue
            self.stdout.write(f"Processing season {season}...")

            results: dict[int, list[tuple[float, float, float, float]]] = {}
            for match in matches:
                home_team = players.setdefault(match.home_team_id, Player())
                away_team = players.setdefault(match.away_team_id, Player())

                home_team_outcome = 0.5
                if match.home_score > match.away_score:
                    home_team_outcome = 1
                elif match.home_score < match.away_score:
                    home_team_outcome = 0
                away_team_outcome = 1 - home_team_outcome

                margin = abs(match.home_score - match.away_score)
                margin_factor = min(margin, MARGIN_WEIGHT_CAP) / MARGIN_WEIGHT_CAP

                results.setdefault(match.home_team_id, []).append(
                    (away_team.rating, away_team.rd, margin_factor, home_team_outcome)
                )
                results.setdefault(match.away_team_id, []).append(
                    (home_team.rating, home_team.rd, margin_factor, away_team_outcome)
                )

            ratings = []
            team_status_updates = []
            for player_id, player in players.items():
                before_rating = player.rating
                before_rd = player.rd
                before_vol = player.vol

                recs = results.get(player_id, [])
                if recs:
                    r_list = [r for r, _, _, _ in recs]
                    rd_list = [rd for _, rd, _, _ in recs]
                    o_list = [0.5 + (o - 0.5) * m for _, _, m, o in recs]
                    player.update_player(r_list, rd_list, o_list)
                    team_status_updates.append((player_id, True))
                else:
                    player.did_not_compete()
                    team_status_updates.append((player_id, False))

                ratings.append(
                    GlickoRating(
                        team_id=player_id,
                        season=season,
                        previous_rating=before_rating,
                        previous_rd=before_rd,
                        previous_vol=before_vol,
                        rating=player.rating,
                        rd=player.rd,
                        vol=player.vol,
                    )
                )

            # Bulk update team active status
            if team_status_updates:
                Team.objects.bulk_update(
                    [
                        Team(id=team_id, active=active)
                        for team_id, active in team_status_updates
                    ],
                    fields=["active"],
                )

            if ratings:
                GlickoRating.objects.bulk_create(
                    ratings, batch_size=500, ignore_conflicts=True
                )
