"""Views related to ranking displays."""

import logging

from django.core.cache import cache
from django.db.models.query import QuerySet
from django.http import Http404
from django.views.generic import ListView

from core.models.enums import DivisionClassification
from core.models.glicko import GlickoRating

logger = logging.getLogger(__name__)


class RankingListView(ListView):
    """Class-based ListView for team rankings."""

    model = GlickoRating
    context_object_name = "ratings"
    template_name = "ranking.html"

    def get_template_names(self) -> list[str]:
        """Return template names, using HTMX variant when requested."""
        if self.request.headers.get("HX-Request"):
            return ["cotton/ranking_table.html"]
        return [self.template_name]

    def get_classification(self) -> str | None:
        """Return the classification parameter if valid."""
        classification = self.kwargs.get("classification")
        if (
            classification
            and classification not in DivisionClassification.values
        ):
            raise Http404
        return classification

    def get_season_and_week(
        self, queryset: QuerySet[GlickoRating]
    ) -> tuple[int | None, int | None, list[int], list[int]]:
        """Determine available seasons and weeks for rankings."""
        classification = self.get_classification() or ""
        # Seasons
        seasons_key = f"ranking_seasons_{classification}"
        seasons = cache.get(seasons_key)
        if seasons is None:
            seasons = list(
                queryset.order_by().values_list("season", flat=True).distinct()
            )
            seasons.sort()
            cache.set(seasons_key, seasons, 3600)
        else:
            logger.debug("Cache hit for seasons: %s", seasons_key)
        latest_season = seasons[-1] if seasons else None
        season = self.request.GET.get("season")
        season = (
            int(season)
            if season and season.isdigit() and int(season) in seasons
            else latest_season
        )

        # Weeks
        weeks_key = f"ranking_weeks_{classification}_{season}"
        weeks = cache.get(weeks_key)
        if weeks is None:
            weeks_qs = (
                queryset.filter(season=season)
                if season is not None
                else queryset
            )
            weeks = list(
                weeks_qs.order_by().values_list("week", flat=True).distinct()
            )
            weeks.sort()
            cache.set(weeks_key, weeks, 3600)
        else:
            logger.debug("Cache hit for weeks: %s", weeks_key)
        latest_week = weeks[-1] if weeks else None
        week = self.request.GET.get("week")
        week = (
            int(week)
            if week and week.isdigit() and int(week) in weeks
            else latest_week
        )

        return season, week, seasons, weeks

    def get_queryset(self) -> QuerySet[GlickoRating]:
        """Return the filtered queryset for rankings."""
        classification = self.get_classification()
        qs = (
            GlickoRating.objects.all()
            .select_related("team")
            .prefetch_related("team__logos", "team__alternative_names")
        )

        if classification:
            qs = qs.filter(classification=classification)

        (
            self.season,
            self.week,
            self.seasons,
            self.weeks,
        ) = self.get_season_and_week(qs)
        # Filter by chosen season and week
        if self.season is not None:
            qs = qs.filter(season=self.season)
        if self.week is not None:
            qs = qs.filter(week=self.week)

        return qs.order_by("-rating")

    def get_context_data(self, **kwargs: object) -> dict[str, object]:
        """Include ranking metadata in the template context."""
        context = super().get_context_data(**kwargs)
        classification = self.get_classification()

        season = getattr(self, "season", None)
        week = getattr(self, "week", None)
        seasons = getattr(self, "seasons", [])
        weeks = getattr(self, "weeks", [])

        classification_label = (
            DivisionClassification(classification).label
            if classification
            else None
        )
        title = (
            f"{classification_label} Rankings"
            if classification_label
            else "Rankings"
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
