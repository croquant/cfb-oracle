from django.contrib import admin
from django.test import TestCase

from core.admin.team_admin import TeamAdmin, TeamLogoInline, VenueInline
from core.models.team import Team, TeamLogo
from core.models.venue import Venue


class TeamLogoInlineTests(TestCase):
    def setUp(self):
        self.team = Team.objects.create(
            school="Logo Team",
            color="#ffffff",
            alternate_color="#000000",
        )
        self.inline = TeamLogoInline(Team, admin.site)

    def test_preview_with_url(self):
        """``preview`` renders an image tag when a logo URL exists."""
        logo = TeamLogo.objects.create(team=self.team, url="http://logo")
        html = self.inline.preview(logo)
        self.assertIn('<img src="http://logo" class="h-16" />', html)

    def test_preview_without_url_uses_placeholder(self):
        """``preview`` falls back to a placeholder when no URL is set."""
        logo = TeamLogo(team=self.team)
        html = self.inline.preview(logo)
        self.assertIn("logo_placeholder.png", html)


class VenueInlineTests(TestCase):
    def setUp(self):
        self.inline = VenueInline(Team, admin.site)

    def test_get_form_queryset_with_location(self):
        """``get_form_queryset`` returns the team's current location."""
        venue = Venue.objects.create(name="Stadium", city="City", state="ST")
        team = Team.objects.create(
            school="Venue Team",
            color="#ffffff",
            alternate_color="#000000",
            location=venue,
        )
        qs = self.inline.get_form_queryset(team)
        self.assertEqual(list(qs), [venue])

    def test_get_form_queryset_without_location(self):
        """``get_form_queryset`` is empty when the team has no location."""
        qs = self.inline.get_form_queryset(None)
        self.assertEqual(list(qs), [])

    def test_save_new_instance_sets_parent_location(self):
        """``save_new_instance`` assigns the venue to the parent team."""
        team = Team.objects.create(
            school="Parent",
            color="#ffffff",
            alternate_color="#000000",
        )
        venue = Venue.objects.create(name="Home", city="Town", state="TS")
        self.inline.save_new_instance(team, venue)
        self.assertEqual(team.location, venue)


class TeamAdminTests(TestCase):
    def setUp(self):
        self.admin = TeamAdmin(Team, admin.site)

    def test_logo_display_returns_html(self):
        """``logo_display`` renders the team's logo when available."""
        team = Team.objects.create(
            school="Display Team",
            color="#ffffff",
            alternate_color="#000000",
        )
        TeamLogo.objects.create(team=team, url="http://display")
        html = self.admin.logo_display(team)
        self.assertIn('<img src="http://display" class="h-8" />', html)

    def test_logo_display_without_logo(self):
        """``logo_display`` is ``None`` when the team has no logos."""
        team = Team.objects.create(
            school="No Logo",
            color="#ffffff",
            alternate_color="#000000",
        )
        self.assertIsNone(self.admin.logo_display(team))
