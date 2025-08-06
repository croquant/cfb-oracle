from django.db.models import Max
from django.shortcuts import render

from core.models.glicko import GlickoRating


# Create your views here.
def index(request):
    latest = GlickoRating.objects.aggregate(Max("season"))
    latest_season = latest["season__max"]
    if latest_season is not None:
        latest_week = (
            GlickoRating.objects.filter(season=latest_season)
            .aggregate(Max("week"))["week__max"]
        )
        latest_ratings = (
            GlickoRating.objects.filter(season=latest_season, week=latest_week)
            .order_by("-rating")
            .select_related("team")
            .prefetch_related("team__logos")
            .filter(team__active=True)
        )[:25]
        # Annotate each rating with the team's first logo URL
        for rating in latest_ratings:
            logo = rating.team.logos.first()
            rating.logo_url = logo.url if logo else None
    else:
        latest_ratings = GlickoRating.objects.none()
    return render(request, "index.html", {"ratings": latest_ratings})
