"""Views related to team details."""

from django.views.generic import DetailView

from core.models.team import Team


class TeamDetailView(DetailView):
    """Display detailed information for a single team."""

    model = Team
    queryset = Team.objects.with_related()
    context_object_name = "team"
    template_name = "team_detail.html"
    slug_field = "slug"
    slug_url_kwarg = "slug"
