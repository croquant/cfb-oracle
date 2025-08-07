from django.urls import path

from .views.index_view import index_view
from .views.ranking_views import RankingListView

urlpatterns = [
    path("", index_view, name="index"),
    path("rankings/<str:classification>/", RankingListView.as_view(), name="rankings"),
]
