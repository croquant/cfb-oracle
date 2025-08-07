from django.core.cache import cache
from django.http import Http404
from django.shortcuts import render

from core.models.enums import DivisionClassification
from core.models.glicko import GlickoRating


def ranking_view(request, classification: str):
    """Ranking view with optional season, week and classification filters."""
    if classification not in DivisionClassification.values:
        raise Http404

    glico_ratings_qs = GlickoRating.objects.filter(active=True).select_related("team")
    if classification:
        glico_ratings_qs = glico_ratings_qs.filter(classification=classification)

    seasons_cache_key = f"ranking_view_seasons_{classification}"
    seasons = cache.get(seasons_cache_key)
    if seasons is None:
        seasons = (
            glico_ratings_qs.order_by().values_list("season", flat=True).distinct()
        )
        cache.set(seasons_cache_key, seasons, 3600)
    latest_season = max(seasons) if seasons else None
    season = request.GET.get("season")
    season = int(season) if season and season.isdigit() else latest_season
    glico_ratings_qs = glico_ratings_qs.filter(season=season)

    season_weeks_cache_key = f"ranking_view_weeks_{classification or 'all'}_{season}"
    weeks = cache.get(season_weeks_cache_key)
    if weeks is None:
        weeks = glico_ratings_qs.order_by().values_list("week", flat=True).distinct()
        cache.set(season_weeks_cache_key, weeks, 3600)
    latest_week = max(weeks) if weeks else None
    week = request.GET.get("week")
    week = int(week) if week and week.isdigit() else latest_week
    glico_ratings_qs = glico_ratings_qs.filter(week=week)

    if season is not None and week is not None:
        ratings = (
            glico_ratings_qs.filter(season=season, week=week)
            .order_by("-rating")
            .select_related("team")
        )
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
        "weeks": weeks,
        "week": week,
        "classification": classification,
        "classification_label": classification_label,
        "title": title,
    }

    template = (
        "cotton/ranking_table.html"
        if request.headers.get("HX-Request")
        else "ranking.html"
    )
    return render(request, template, context)
