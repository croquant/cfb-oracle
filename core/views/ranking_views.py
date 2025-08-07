from django.core.cache import cache
from django.http import Http404
from django.views.generic import ListView

from core.models.enums import DivisionClassification
from core.models.glicko import GlickoRating


class RankingListView(ListView):
    """Class-based ListView for team rankings."""

    model = GlickoRating
    context_object_name = "ratings"
    template_name = "ranking.html"

    def get_template_names(self):
        # Use HTMX-specific template if requested
        if self.request.headers.get("HX-Request"):
            return ["cotton/ranking_table.html"]
        return [self.template_name]

    def get_classification(self):
        classification = self.kwargs.get("classification")
        if classification and classification not in DivisionClassification.values:
            raise Http404
        return classification

    def get_season_and_week(self, queryset):
        classification = self.get_classification() or ""
        # Seasons
        seasons_key = f"ranking_seasons_{classification}"
        seasons = cache.get(seasons_key)
        if seasons is None:
            seasons = list(
                queryset.order_by().values_list("season", flat=True).distinct()
            )
            cache.set(seasons_key, seasons, 3600)
        latest_season = max(seasons) if seasons else None
        season = self.request.GET.get("season")
        season = int(season) if season and season.isdigit() else latest_season

        # Weeks
        weeks_key = f"ranking_weeks_{classification}_{season}"
        weeks = cache.get(weeks_key)
        if weeks is None:
            weeks_qs = (
                queryset.filter(season=season) if season is not None else queryset
            )
            weeks = list(weeks_qs.order_by().values_list("week", flat=True).distinct())
            cache.set(weeks_key, weeks, 3600)
        latest_week = max(weeks) if weeks else None
        week = self.request.GET.get("week")
        week = int(week) if week and week.isdigit() else latest_week

        return season, week, seasons, weeks

    def get_queryset(self):
        classification = self.get_classification()
        qs = GlickoRating.objects.filter(active=True).select_related("team")

        if classification:
            qs = qs.filter(classification=classification)

        season, week, seasons, weeks = self.get_season_and_week(qs)
        # Filter by chosen season and week
        if season is not None:
            qs = qs.filter(season=season)
        if week is not None:
            qs = qs.filter(week=week)

        return qs.order_by("-rating")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        classification = self.get_classification()
        season, week, seasons, weeks = self.get_season_and_week(
            GlickoRating.objects.filter(active=True)
            .select_related("team")
            .filter(classification=classification)
            if classification
            else GlickoRating.objects.filter(active=True).select_related("team")
        )

        classification_label = (
            DivisionClassification(classification).label if classification else None
        )
        title = (
            f"{classification_label} Rankings" if classification_label else "Rankings"
        )

        context.update(
            {
                "seasons": seasons,
                "season": season,
                "weeks": weeks,
                "week": week,
                "classification": classification,
                "classification_label": classification_label,
                "title": title,
            }
        )
        return context
