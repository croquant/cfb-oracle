"""Admin configuration for team-related models."""

from django.contrib import admin
from django.db.models.query import QuerySet
from django.templatetags.static import static
from django.utils.html import format_html
from unfold.admin import ModelAdmin, TabularInline
from unfold.contrib.inlines.admin import NonrelatedStackedInline

from core.models.team import Team, TeamAlternativeName, TeamLogo
from core.models.venue import Venue


class TeamAlternativeNameTabularInline(TabularInline):
    """Inline for alternative team names."""

    model = TeamAlternativeName
    fields = ("name",)
    extra = 0
    hide_title = True
    tab = True


class TeamLogoInline(TabularInline):
    """Inline for team logos with preview."""

    model = TeamLogo
    fields = ("url", "preview")
    readonly_fields = ("preview",)
    extra = 0
    hide_title = True
    tab = True

    def preview(self, obj: TeamLogo) -> str:
        """Render a preview of the logo."""
        if obj.url:
            return format_html(f'<img src="{obj.url}" class="h-16" />')
        placeholder_url = static("images/logo_placeholder.png")
        return format_html(f'<img src="{placeholder_url}" class="h-16" />')

    preview.short_description = "Logo"


class VenueInline(NonrelatedStackedInline):
    """Inline for venue information associated with a team."""

    model = Venue
    extra = 0
    max_num = 1
    can_delete = False
    hide_title = True
    tab = True
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "name",
                    ("city", "state"),
                    ("zip_code", "country_code"),
                    "timezone",
                    ("latitude", "longitude"),
                    "elevation",
                    "capacity",
                    "construction_year",
                    ("grass", "dome"),
                )
            },
        ),
    )

    def get_form_queryset(self, obj: Team | None) -> QuerySet[Venue]:
        """Return queryset for the inline form."""
        if obj and obj.location:
            return Venue.objects.filter(pk=obj.location.pk)
        return Venue.objects.none()

    def save_new_instance(self, parent: Team, obj: Venue) -> None:
        """Persist the newly created venue on the team."""
        parent.location = obj


@admin.register(Team)
class TeamAdmin(ModelAdmin):
    """Admin configuration for the Team model."""

    search_fields = ("school", "mascot")
    list_display = (
        "logo_display",
        "school",
        "mascot",
        "abbreviation",
        "conference",
    )
    list_select_related = ("location", "conference")
    list_filter = (
        "classification",
        "conference",
    )
    list_filter_sheet = False
    prepopulated_fields = {"slug": ("school",)}
    inlines = [VenueInline, TeamAlternativeNameTabularInline, TeamLogoInline]
    fieldsets = (
        (
            None,
            {
                "fields": (
                    ("school", "mascot"),
                    ("slug", "abbreviation"),
                    ("classification", "conference"),
                    ("color", "alternate_color"),
                    "twitter",
                ),
            },
        ),
    )

    def logo_display(self, obj: Team) -> str | None:
        """Render the team's logo or return ``None`` if missing."""
        logo = obj.logos.first()
        if logo:
            return format_html(f'<img src="{logo.url}" class="h-8" />')
        return None

    logo_display.short_description = "Logo"
