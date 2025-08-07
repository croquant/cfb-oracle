from django.urls import path

from .views import ranking_view

urlpatterns = [
    path("", ranking_view, name="index"),
    path("rankings/<str:classification>/", ranking_view, name="rankings"),
]
