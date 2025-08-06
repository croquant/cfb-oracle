import json
from collections import defaultdict
from django.core.cache import cache
from django.shortcuts import render

from core.models.glicko import GlickoRating


def index(request):
    """Ranking view with optional season and week filters."""
    # Build mapping of seasons to available weeks (cached)
    weeks = cache.get("season_weeks")
    if weeks is None:
        season_weeks = (
            GlickoRating.objects.order_by("season", "week")
            .values("season", "week")
            .distinct()
        )
        weeks_dict = defaultdict(list)
        for row in season_weeks:
            weeks_dict[row["season"]].append(row["week"])
        weeks = dict(weeks_dict)
        cache.set("season_weeks", weeks, 3600)

    seasons = sorted(weeks.keys())
    latest_season = seasons[-1] if seasons else None
    season = request.GET.get("season")
    season = int(season) if season else latest_season

    season_weeks_list = weeks.get(season, [])
    latest_week = season_weeks_list[-1] if season_weeks_list else None
    week = request.GET.get("week")
    week = int(week) if week else latest_week

    if season is not None and week is not None:
        ratings = (
            GlickoRating.objects.filter(season=season, week=week)
            .order_by("-rating")
            .select_related("team")
            .prefetch_related("team__logos")
            .filter(team__active=True)
        )[:25]
    else:
        ratings = GlickoRating.objects.none()

    for rating in ratings:
        logo = rating.team.logos.first()
        rating.logo_url = logo.url if logo else None

    context = {
        "ratings": ratings,
        "seasons": seasons,
        "season": season,
        "week": week,
        "weeks_json": json.dumps(weeks),
    }

    template = "cotton/ranking_table.html" if request.headers.get("HX-Request") else "index.html"
    return render(request, template, context)
