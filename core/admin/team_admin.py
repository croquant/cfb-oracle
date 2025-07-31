from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline

from core.models.team import Team, TeamAlternativeName, TeamLogo


class TeamAlternativeNameTabularInline(TabularInline):
    model = TeamAlternativeName
    fields = ("name",)
    extra = 0
    hide_title = True


class TeamLogoInline(TabularInline):
    model = TeamLogo
    fields = ("url",)
    extra = 0


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

