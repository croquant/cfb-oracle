from django.urls import path

from .views.index_view import index_view
from .views.ranking_views import ranking_view

urlpatterns = [
    path("", index_view, name="index"),
    path("rankings/<str:classification>/", ranking_view, name="rankings"),
]
