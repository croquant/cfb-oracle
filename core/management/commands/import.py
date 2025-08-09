import os
import time
from datetime import date

import cfbd
from cfbd.rest import ApiException
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from dotenv import load_dotenv

from core.models.conference import Conference
from core.models.match import Match
from core.models.team import Team, TeamAlternativeName, TeamLogo
from core.models.venue import Venue


class Command(BaseCommand):
    help = "Imports data from CFBD API"

    def add_arguments(self, parser):
        parser.add_argument(
            "--conference",
            type=str,
            help="Optional conference abbreviation filter",
        )
        parser.add_argument(
            "--year",
            type=int,
            help=(
                "Optional year filter to get historical "
                "conference affiliations"
            ),
        )
        parser.add_argument(
            "--start-year",
            type=int,
            default=1869,
            help="First season year to import games from",
        )
        parser.add_argument(
            "--end-year",
            type=int,
            default=date.today().year,
            help="Last season year to import games from",
        )

    def import_venues(self, api_instance):
        """Fetch venue data from CFBD and store it in the database.

        Steps:
        1. Call :func:`VenuesApi.get_venues` to retrieve all venues.
        2. Loop over the response and ``update_or_create`` each :class:`Venue`.
        3. Output a status line for every processed venue.
        """

        venues_response = api_instance.get_venues()
        for venue in venues_response:
            Venue.objects.update_or_create(
                id=venue.id,
                defaults={
                    "name": venue.name,
                    "city": venue.city,
                    "state": venue.state,
                    "zip_code": venue.zip,
                    "country_code": venue.country_code,
                    "timezone": venue.timezone,
                    "latitude": venue.latitude,
                    "longitude": venue.longitude,
                    "elevation": float(venue.elevation)
                    if venue.elevation
                    else None,
                    "capacity": venue.capacity,
                    "construction_year": venue.construction_year,
                    "grass": venue.grass,
                    "dome": venue.dome,
                },
            )
            self.stdout.write(
                f"Venue {venue.name} ({venue.city}, {venue.state}) "
                "imported/updated successfully."
            )

    def import_conferences(self, api_instance):
        """Fetch conference information and save it to the database.

        Steps:
        1. Retrieve conferences using :func:`ConferencesApi.get_conferences`.
        2. ``update_or_create`` each :class:`Conference` object.
        3. Output a status message for every processed conference.
        """

        conferences_response = api_instance.get_conferences()
        for conf in conferences_response:
            Conference.objects.update_or_create(
                id=conf.id,
                defaults={
                    "name": conf.name,
                    "short_name": conf.short_name,
                    "abbreviation": conf.abbreviation,
                    "classification": conf.classification,
                },
            )
            self.stdout.write(
                f"Conference {conf.name} imported/updated successfully."
            )

    def import_teams(self, api_instance, *, conference=None, year=None):
        """Fetch team data and related records from CFBD.

        Steps:
        1. Call :func:`TeamsApi.get_teams` with optional ``conference`` and
           ``year``.
        2. Create or update :class:`Team` instances, including venue and
           conference links.
        3. Store associated :class:`TeamLogo` and
           :class:`TeamAlternativeName` records.
        4. Output a status line for every processed team.
        """

        teams_response = api_instance.get_teams(
            conference=conference, year=year
        )

        # Preload related objects so we do not hit the database for every team
        # iteration. ``in_bulk`` performs a single query returning a dictionary
        # of objects keyed by the requested field, in this case the primary key.
        # We then construct lookup dictionaries keyed by abbreviation and name
        # from that result set.
        conferences = Conference.objects.in_bulk()
        conferences_by_abbrev = {
            c.abbreviation: c for c in conferences.values() if c.abbreviation
        }
        conferences_by_name = {
            c.name: c for c in conferences.values() if c.name
        }

        # ``in_bulk`` without ``field_name`` defaults to the primary key, which
        # is already unique for venues. We can therefore use the returned
        # dictionary directly for ID lookups.
        venues_by_id = Venue.objects.in_bulk()

        for team in teams_response:
            conference_obj = None
            if team.conference:
                conference_obj = conferences_by_abbrev.get(
                    team.conference
                ) or conferences_by_name.get(team.conference)

            new_team, _ = Team.objects.update_or_create(
                id=team.id,
                defaults={
                    "school": team.school,
                    "mascot": team.mascot,
                    "abbreviation": team.abbreviation,
                    "conference": conference_obj,
                    "classification": team.classification,
                    "color": team.color,
                    "alternate_color": team.alternate_color,
                    "twitter": team.twitter,
                    "location": (
                        venues_by_id.get(team.location.id)
                        if team.location and team.location.id
                        else None
                    ),
                },
            )
            for logo in team.logos or []:
                TeamLogo.objects.update_or_create(
                    team=new_team,
                    url=logo,
                )
            for alt_name in team.alternate_names or []:
                TeamAlternativeName.objects.update_or_create(
                    team=new_team,
                    name=alt_name,
                )
            self.stdout.write(
                f"Team {team.school} ({team.abbreviation}) "
                "imported/updated successfully."
            )

    def import_games(self, api_instance, *, start_year, end_year):
        """Fetch game data and store it using the :class:`Match` model.

        Steps:
        1. Loop over the supplied year range and call
           :func:`GamesApi.get_games`.
        2. ``update_or_create`` each :class:`Match` instance linking teams,
           venues, and conferences where possible.
        3. Output a status line for every processed game.
        """

        # Preload related objects for efficient lookup during import
        teams_by_id = Team.objects.in_bulk()
        venues_by_id = Venue.objects.in_bulk()
        conferences = Conference.objects.in_bulk()
        conferences_by_abbrev = {
            c.abbreviation: c for c in conferences.values() if c.abbreviation
        }
        conferences_by_name = {
            c.name: c for c in conferences.values() if c.name
        }

        for season in range(start_year, end_year + 1):
            games_response = api_instance.get_games(
                year=season, season_type=cfbd.SeasonType.BOTH
            )
            for game in games_response:
                start_date = game.start_date
                if timezone.is_naive(start_date):
                    start_date = timezone.make_aware(start_date)
                Match.objects.update_or_create(
                    id=game.id,
                    defaults={
                        "season": game.season,
                        "week": game.week,
                        "season_type": game.season_type.value,
                        "start_date": start_date,
                        "completed": game.completed,
                        "venue": venues_by_id.get(game.venue_id),
                        "neutral_site": game.neutral_site,
                        "attendance": game.attendance,
                        "home_team": teams_by_id.get(game.home_id),
                        "home_classification": (
                            game.home_classification.value
                            if game.home_classification
                            else None
                        ),
                        "home_conference": conferences_by_abbrev.get(
                            game.home_conference
                        )
                        or conferences_by_name.get(game.home_conference),
                        "home_score": game.home_points,
                        "away_team": teams_by_id.get(game.away_id),
                        "away_classification": (
                            game.away_classification.value
                            if game.away_classification
                            else None
                        ),
                        "away_conference": conferences_by_abbrev.get(
                            game.away_conference
                        )
                        or conferences_by_name.get(game.away_conference),
                        "away_score": game.away_points,
                    },
                )
                self.stdout.write(
                    f"Match {game.home_team} vs {game.away_team} ({season}) "
                    "imported/updated successfully."
                )

    def handle(self, *args, **options):
        load_dotenv()
        api_key = os.environ.get("CFBD_API_KEY")
        if not api_key:
            raise CommandError("CFBD_API_KEY environment variable not set")

        configuration = cfbd.Configuration(access_token=api_key)

        with cfbd.ApiClient(configuration) as api_client:
            venues_api_instance = cfbd.VenuesApi(api_client)
            teams_api_instance = cfbd.TeamsApi(api_client)
            conferences_api_instance = cfbd.ConferencesApi(api_client)
            games_api_instance = cfbd.GamesApi(api_client)
            total_start = time.perf_counter()

            try:
                step_start = time.perf_counter()
                self.import_venues(venues_api_instance)
                self.stdout.write(
                    f"Venues import completed in "
                    f"{time.perf_counter() - step_start:.2f} seconds"
                )

                step_start = time.perf_counter()
                self.import_conferences(conferences_api_instance)
                self.stdout.write(
                    f"Conferences import completed in "
                    f"{time.perf_counter() - step_start:.2f} seconds"
                )

                step_start = time.perf_counter()
                self.import_teams(
                    teams_api_instance,
                    conference=options.get("conference"),
                    year=options.get("year"),
                )
                self.stdout.write(
                    f"Teams import completed in "
                    f"{time.perf_counter() - step_start:.2f} seconds"
                )

                step_start = time.perf_counter()
                self.import_games(
                    games_api_instance,
                    start_year=options.get("start_year"),
                    end_year=options.get("end_year"),
                )
                self.stdout.write(
                    f"Games import completed in "
                    f"{time.perf_counter() - step_start:.2f} seconds"
                )
            except ApiException as e:
                self.stderr.write(f"Exception when calling CFBD API: {e}\n")
            finally:
                total_elapsed = time.perf_counter() - total_start
                self.stdout.write(
                    f"Total import completed in {total_elapsed:.2f} seconds"
                )
