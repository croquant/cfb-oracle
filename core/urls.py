"""URL routing configuration for the core app."""

from django.urls import path

from .views.index_view import index_view
from .views.ranking_views import RankingListView
from .views.team_views import TeamDetailView

urlpatterns = [
    path("", index_view, name="index"),
    path(
        "rankings/<str:classification>/",
        RankingListView.as_view(),
        name="rankings",
    ),
    path(
        "teams/<slug:slug>/",
        TeamDetailView.as_view(),
        name="team-detail",
    ),
]
