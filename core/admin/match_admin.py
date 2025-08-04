from django.contrib import admin
from unfold.admin import ModelAdmin

from core.models.match import Match


@admin.register(Match)
class MatchAdmin(ModelAdmin):
    list_display = (
        "start_date",
        "season",
        "week",
        "season_type",
        "home_team",
        "home_score",
        "away_team",
        "away_score",
        "venue",
        "completed",
    )
    list_filter = (
        "season",
        "season_type",
        "completed",
    )
    search_fields = (
        "home_team__school",
        "home_team__mascot",
        "away_team__school",
        "away_team__mascot",
    )
    list_select_related = (
        "home_team",
        "away_team",
        "venue",
        "home_conference",
        "away_conference",
    )
    list_filter_sheet = False
