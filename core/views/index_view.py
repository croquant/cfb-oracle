"""View for the home page."""

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render


def index_view(request: HttpRequest) -> HttpResponse:
    """Render the index page."""
    return render(request, "index.html")
