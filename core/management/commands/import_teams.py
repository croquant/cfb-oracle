import os

import cfbd
from cfbd.rest import ApiException
from django.core.management.base import BaseCommand
from dotenv import load_dotenv

from core.models.team import Team, TeamAlternativeName, TeamLogo
from core.models.venue import Venue

load_dotenv()

configuration = cfbd.Configuration(access_token=os.environ["CFBD_API_KEY"])


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

    def handle(self, *args, **options):
        with cfbd.ApiClient(configuration) as api_client:
            venues_api_instance = cfbd.VenuesApi(api_client)
            teams_api_instance = cfbd.TeamsApi(api_client)

            try:
                venues_response = venues_api_instance.get_venues()
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
                            "elevation": venue.elevation,
                            "capacity": venue.capacity,
                            "construction_year": venue.construction_year,
                            "grass": venue.grass,
                            "dome": venue.dome,
                        },
                    )
                    self.stdout.write(
                        f"Venue {venue.name} ({venue.city}, {venue.state}) imported/updated successfully."
                    )

                teams_response = teams_api_instance.get_teams(
                    conference=options.get("conference"),
                    year=options.get("year"),
                )
                for team in teams_response:
                    new_team, _ = Team.objects.update_or_create(
                        id=team.id,
                        defaults={
                            "school": team.school,
                            "mascot": team.mascot,
                            "abbreviation": team.abbreviation,
                            "conference": team.conference,
                            "classification": team.classification,
                            "color": team.color,
                            "alternate_color": team.alternate_color,
                            "twitter": team.twitter,
                            "location": Venue.objects.get(id=team.location.id)
                            if team.location and team.location.id
                            else None,
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

            except ApiException as e:
                self.stderr.write(f"Exception when calling TeamsApi->get_teams: {e}\n")
