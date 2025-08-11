"""View for the home page."""

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.utils import timezone

from core.models.glicko import GlickoRating
from core.models.match import Match


def index_view(request: HttpRequest) -> HttpResponse:
    """Render the index page with dashboard data."""
    upcoming_games = Match.objects.filter(
        start_date__gte=timezone.now()
    ).order_by("start_date")[:5]
    top_teams = GlickoRating.objects.filter(active=True).order_by("-rating")[:5]
    context = {"upcoming_games": upcoming_games, "top_teams": top_teams}
    return render(request, "index.html", context)
