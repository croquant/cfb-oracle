import os

import cfbd
from cfbd.rest import ApiException
from django.core.management.base import BaseCommand, CommandError
from dotenv import load_dotenv

from core.models.conference import Conference
from core.models.team import Team, TeamAlternativeName, TeamLogo
from core.models.venue import Venue


class Command(BaseCommand):
    help = "Imports teams from CFBD API"

    def add_arguments(self, parser):
        parser.add_argument(
            "--conference", type=str, help="Optional conference abbreviation filter"
        )
        parser.add_argument(
            "--year",
            type=int,
            help="Optional year filter to get historical conference affiliations",
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
                    "elevation": float(venue.elevation) if venue.elevation else None,
                    "capacity": venue.capacity,
                    "construction_year": venue.construction_year,
                    "grass": venue.grass,
                    "dome": venue.dome,
                },
            )
            self.stdout.write(
                f"Venue {venue.name} ({venue.city}, {venue.state}) imported/updated successfully."
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
        1. Call :func:`TeamsApi.get_teams` with optional ``conference`` and ``year``.
        2. Create or update :class:`Team` instances including venue and conference links.
        3. Store associated :class:`TeamLogo` and :class:`TeamAlternativeName` records.
        4. Output a status line for every processed team.
        """

        teams_response = api_instance.get_teams(conference=conference, year=year)

        # Preload related objects so we do not hit the database for every team
        # iteration. ``in_bulk`` performs a single query returning a dictionary
        # of objects keyed by the requested field, in this case the primary key.
        # We then construct lookup dictionaries keyed by abbreviation and name
        # from that result set.
        conferences = Conference.objects.in_bulk()
        conferences_by_abbrev = {
            c.abbreviation: c for c in conferences.values() if c.abbreviation
        }
        conferences_by_name = {c.name: c for c in conferences.values()}

        # ``in_bulk`` without ``field_name`` defaults to the primary key, which
        # is already unique for venues. We can therefore use the returned
        # dictionary directly for ID lookups.
        venues_by_id = Venue.objects.in_bulk()

        for team in teams_response:
            conference_obj = None
            if team.conference:
                conference_obj = (
                    conferences_by_abbrev.get(team.conference)
                    or conferences_by_name.get(team.conference)
                )

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
                f"Team {team.school} ({team.abbreviation}) imported/updated successfully."
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

            try:
                self.import_venues(venues_api_instance)
                self.import_conferences(conferences_api_instance)
                self.import_teams(
                    teams_api_instance,
                    conference=options.get("conference"),
                    year=options.get("year"),
                )
            except ApiException as e:
                self.stderr.write(f"Exception when calling CFBD API: {e}\n")
