import io
from argparse import ArgumentParser
from datetime import date, datetime
from importlib import import_module
from types import SimpleNamespace as NS
from unittest.mock import MagicMock, patch

import cfbd
from cfbd.rest import ApiException
from django.core.management.base import CommandError
from django.test import TestCase
from django.utils import timezone
from core.models.conference import Conference
from core.models.match import Match
from core.models.team import Team
from core.models.venue import Venue

Command = import_module("core.management.commands.import").Command


class ImportCommandTests(TestCase):
    """Tests for the CFBD import management command."""

    def setUp(self):
        self.command = Command()
        self.command.stdout = io.StringIO()
        self.command.stderr = io.StringIO()

    def _ns(self, **kwargs):
        """Shorthand for creating simple namespaces."""
        return NS(**kwargs)

    def _sample_venue(self, capacity: int = 55000):
        return self._ns(
            id=1,
            name="Bobby Dodd Stadium",
            city="Atlanta",
            state="GA",
            zip="30332",
            country_code="US",
            timezone="America/New_York",
            latitude=33.7725,
            longitude=-84.3928,
            elevation=0,
            capacity=capacity,
            construction_year=1913,
            grass=True,
            dome=False,
        )

    def _sample_conference(self, name: str = "Atlantic Coast Conference"):
        return self._ns(
            id=1,
            name=name,
            short_name="ACC",
            abbreviation="ACC",
            classification="fbs",
        )

    def _import_prerequisites(self):
        """Import a sample venue and conference for team/game tests."""
        venue_api = self._ns(get_venues=lambda: [self._sample_venue()])
        self.command.import_venues(venue_api)
        conf_api = self._ns(get_conferences=lambda: [self._sample_conference()])
        self.command.import_conferences(conf_api)

    def _teams_payload(self):
        return [
            self._ns(
                id=1,
                school="Georgia Tech",
                mascot="Yellow Jackets",
                abbreviation="GT",
                conference="ACC",
                classification="fbs",
                color="#000000",
                alternate_color="#FFFFFF",
                twitter="@GTFootball",
                location=self._ns(id=1),
                logos=["logo1", "logo2"],
                alternate_names=["Ga Tech", "Jackets"],
            ),
            self._ns(
                id=2,
                school="Georgia",
                mascot=None,
                abbreviation="UGA",
                conference="Atlantic Coast Conference",
                classification="fbs",
                color="#111111",
                alternate_color="#222222",
                twitter=None,
                location=self._ns(id=1),
                logos=None,
                alternate_names=None,
            ),
            self._ns(
                id=3,
                school="Independent",
                mascot=None,
                abbreviation="IND",
                conference=None,
                classification="fbs",
                color="#333333",
                alternate_color="#444444",
                twitter=None,
                location=None,
                logos=[],
                alternate_names=[],
            ),
        ]

    def _import_sample_teams(self):
        teams = self._teams_payload()
        api = self._ns(get_teams=lambda conference=None, year=None: teams)
        self.command.import_teams(api)
        return teams

    def test_add_arguments(self):
        """``add_arguments`` defines all expected options with defaults."""
        parser = ArgumentParser()
        self.command.add_arguments(parser)
        args = parser.parse_args([])
        self.assertIsNone(args.conference)
        self.assertIsNone(args.year)
        self.assertEqual(args.start_year, 1869)
        self.assertEqual(args.end_year, date.today().year)

    def test_import_venues(self):
        """``import_venues`` creates and updates :class:`Venue` records."""
        venues = [self._sample_venue()]
        api = self._ns(get_venues=lambda: venues)
        self.command.import_venues(api)
        self.assertEqual(Venue.objects.count(), 1)
        venue = Venue.objects.get(id=1)
        self.assertEqual(venue.name, "Bobby Dodd Stadium")

        # Update existing venue
        venues[0] = self._sample_venue(capacity=56000)
        self.command.import_venues(api)
        venue.refresh_from_db()
        self.assertEqual(venue.capacity, 56000)

    def test_import_conferences(self):
        """``import_conferences`` creates and updates Conference records."""
        conferences = [self._sample_conference()]
        api = self._ns(get_conferences=lambda: conferences)
        self.command.import_conferences(api)
        self.assertEqual(Conference.objects.count(), 1)
        conf = Conference.objects.get(id=1)
        self.assertEqual(conf.name, "Atlantic Coast Conference")

        # Update conference name
        conferences[0] = self._sample_conference(name="ACC Updated")
        self.command.import_conferences(api)
        conf.refresh_from_db()
        self.assertEqual(conf.name, "ACC Updated")

    def test_import_teams(self):
        """``import_teams`` creates and updates teams and related records."""
        self._import_prerequisites()
        teams = self._import_sample_teams()

        t1 = Team.objects.get(id=1)
        t2 = Team.objects.get(id=2)
        t3 = Team.objects.get(id=3)

        self.assertEqual(t1.conference.abbreviation, "ACC")
        self.assertEqual(t1.location.name, "Bobby Dodd Stadium")
        self.assertEqual(t1.logos.count(), 2)
        self.assertEqual(t1.alternative_names.count(), 2)

        self.assertEqual(t2.conference.name, "Atlantic Coast Conference")
        self.assertEqual(t2.logos.count(), 0)

        self.assertIsNone(t3.conference)
        self.assertIsNone(t3.location)

        # Update team color and ensure related objects aren't duplicated
        teams[0].color = "#FF0000"
        api_updated = self._ns(
            get_teams=lambda conference=None, year=None: [teams[0]]
        )
        self.command.import_teams(api_updated)
        t1.refresh_from_db()
        self.assertEqual(t1.color, "#FF0000")
        self.assertEqual(t1.logos.count(), 2)
        self.assertEqual(t1.alternative_names.count(), 2)

    def test_import_games(self):
        """``import_games`` creates and updates :class:`Match` records."""
        self._import_prerequisites()
        self._import_sample_teams()

        aware_start = timezone.make_aware(datetime(2023, 9, 8))
        games_by_year = {
            2023: [
                self._ns(
                    id=10,
                    season=2023,
                    week=1,
                    season_type=cfbd.SeasonType.REGULAR,
                    start_date=datetime(2023, 9, 1),
                    completed=True,
                    venue_id=1,
                    neutral_site=False,
                    attendance=1000,
                    home_id=1,
                    home_classification=self._ns(value="fbs"),
                    home_conference="ACC",
                    home_points=28,
                    home_team="Georgia Tech",
                    away_id=2,
                    away_classification=None,
                    away_conference="Atlantic Coast Conference",
                    away_points=14,
                    away_team="Georgia",
                ),
                self._ns(
                    id=11,
                    season=2023,
                    week=2,
                    season_type=cfbd.SeasonType.REGULAR,
                    start_date=aware_start,
                    completed=False,
                    venue_id=1,
                    neutral_site=True,
                    attendance=None,
                    home_id=3,
                    home_classification=None,
                    home_conference="Atlantic Coast Conference",
                    home_points=0,
                    home_team="Independent",
                    away_id=1,
                    away_classification=self._ns(value="fbs"),
                    away_conference=None,
                    away_points=0,
                    away_team="Georgia Tech",
                ),
            ]
        }
        api = self._ns(get_games=lambda year, season_type: games_by_year[year])
        self.command.import_games(api, start_year=2023, end_year=2023)

        m1 = Match.objects.get(id=10)
        m2 = Match.objects.get(id=11)

        self.assertTrue(timezone.is_aware(m1.start_date))
        self.assertEqual(m2.start_date, aware_start)

        self.assertEqual(m1.home_team_id, 1)
        self.assertEqual(m1.home_conference.abbreviation, "ACC")
        self.assertEqual(m1.away_conference.name, "Atlantic Coast Conference")

        self.assertEqual(m2.home_team_id, 3)
        self.assertIsNone(m2.away_conference)

        # Update score
        games_by_year[2023][0].home_points = 30
        games_by_year[2023][0].away_points = 20
        self.command.import_games(api, start_year=2023, end_year=2023)
        m1.refresh_from_db()
        self.assertEqual(m1.home_score, 30)
        self.assertEqual(m1.away_score, 20)

    @patch("core.management.commands.import.load_dotenv")
    def test_handle_requires_api_key(self, mock_load_dotenv):
        """``handle`` raises :class:`CommandError` when API key is missing."""
        with patch.dict("os.environ", {}, clear=True):
            with self.assertRaises(CommandError):
                self.command.handle(
                    conference=None,
                    year=None,
                    start_year=2023,
                    end_year=2023,
                )

    @patch("core.management.commands.import.cfbd.ApiClient")
    @patch("core.management.commands.import.cfbd.GamesApi")
    @patch("core.management.commands.import.cfbd.TeamsApi")
    @patch("core.management.commands.import.cfbd.ConferencesApi")
    @patch("core.management.commands.import.cfbd.VenuesApi")
    def test_handle_api_exception(
        self, mock_venues, mock_confs, mock_teams, mock_games, mock_client
    ):
        """``handle`` catches :class:`ApiException` and logs it to stderr."""
        mock_client.return_value.__enter__.return_value = object()
        mock_client.return_value.__exit__.return_value = False

        self.command.import_venues = MagicMock(side_effect=ApiException("boom"))
        self.command.import_conferences = MagicMock()
        self.command.import_teams = MagicMock()
        self.command.import_games = MagicMock()

        with patch.dict("os.environ", {"CFBD_API_KEY": "token"}):
            self.command.handle(
                conference=None, year=None, start_year=2023, end_year=2023
            )

        self.command.import_venues.assert_called_once()
        self.command.import_conferences.assert_not_called()
        self.assertIn(
            "Exception when calling CFBD API", self.command.stderr.getvalue()
        )
        self.assertIn("Total import completed", self.command.stdout.getvalue())

    @patch("core.management.commands.import.cfbd.ApiClient")
    @patch("core.management.commands.import.cfbd.GamesApi")
    @patch("core.management.commands.import.cfbd.TeamsApi")
    @patch("core.management.commands.import.cfbd.ConferencesApi")
    @patch("core.management.commands.import.cfbd.VenuesApi")
    def test_handle_success(
        self, mock_venues, mock_confs, mock_teams, mock_games, mock_client
    ):
        """``handle`` runs all import steps when API key is present."""
        mock_client.return_value.__enter__.return_value = object()
        mock_client.return_value.__exit__.return_value = False

        self.command.import_venues = MagicMock()
        self.command.import_conferences = MagicMock()
        self.command.import_teams = MagicMock()
        self.command.import_games = MagicMock()

        with patch.dict("os.environ", {"CFBD_API_KEY": "token"}):
            self.command.handle(
                conference="ACC", year=2023, start_year=2023, end_year=2023
            )

        self.command.import_venues.assert_called_once()
        self.command.import_conferences.assert_called_once()
        self.command.import_teams.assert_called_once()
        self.command.import_games.assert_called_once()
        self.assertIn("Total import completed", self.command.stdout.getvalue())
