from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline
from django.utils.translation import gettext_lazy as _

from core.models.team import Team, TeamAlternativeName, TeamLogo


class TeamAlternativeNameTabularInline(TabularInline):
    model = TeamAlternativeName
    hide_title = True


class TeamLogoInline(TabularInline):
    model = TeamLogo


@admin.register(Team)
class TeamAdmin(ModelAdmin):
    search_fields = ("school", "mascot")
    list_display = (
        "school",
        "mascot",
        "abbreviation",
        "conference",
    )
    list_filter = (
        "classification",
        "conference",
    )
    list_filter_sheet = False
    inlines = [TeamAlternativeNameTabularInline, TeamLogoInline]

    fieldsets = (
        (
            _("Basic Info"),
            {
                "fields": (
                    "school",
                    "mascot",
                    "abbreviation",
                    "slug",
                    "conference",
                    "classification",
                )
            },
        ),
        (
            _("Colors & Social"),
            {
                "fields": (
                    "color",
                    "alternate_color",
                    "twitter",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            _("Location"),
            {
                "fields": (
                    "location",
                ),
                "classes": ("collapse",),
            },
        ),
    )


@admin.register(TeamAlternativeName)
class TeamAlternativeNameAdmin(ModelAdmin):
    list_display = (
        "team",
        "name",
    )


@admin.register(TeamLogo)
class TeamLogoAdmin(ModelAdmin):
    list_display = (
        "team",
        "url",
    )
