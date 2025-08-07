import json
from collections import defaultdict

from django.core.cache import cache
from django.http import Http404
from django.shortcuts import render

from core.models.enums import DivisionClassification
from core.models.glicko import GlickoRating


def index(request, classification: str | None = None):
    """Ranking view with optional season, week and classification filters."""
    if classification and classification not in DivisionClassification.values:
        raise Http404

    cache_key = f"season_weeks_{classification or 'all'}"
    weeks = cache.get(cache_key)
    if weeks is None:
        season_weeks_qs = GlickoRating.objects.order_by("season", "week")
        if classification:
            season_weeks_qs = season_weeks_qs.filter(
                team__classification=classification
            )
        season_weeks = season_weeks_qs.values("season", "week").distinct()
        weeks_dict = defaultdict(list)
        for row in season_weeks:
            weeks_dict[row["season"]].append(row["week"])
        weeks = dict(weeks_dict)
        cache.set(cache_key, weeks, 3600)

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
            .filter(active=True)
        )[:25]
    else:
        ratings = GlickoRating.objects.none()

    classification_label = (
        DivisionClassification(classification).label if classification else None
    )
    title = f"{classification_label} Rankings" if classification_label else "Rankings"

    context = {
        "ratings": ratings,
        "seasons": seasons,
        "season": season,
        "week": week,
        "weeks_json": json.dumps(weeks),
        "classification": classification,
        "classification_label": classification_label,
        "title": title,
    }

    template = (
        "cotton/ranking_table.html"
        if request.headers.get("HX-Request")
        else "index.html"
    )
    return render(request, template, context)
