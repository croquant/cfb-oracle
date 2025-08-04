from django.contrib import admin
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.urls import NoReverseMatch, path, reverse

from core.models.match import Match
from core.models.team import Team


def team_info_page(request):
    context = admin.site.each_context(request)
    return render(request, "admin/team_info.html", context)


def team_search(request):
    query = request.GET.get("q", "")
    teams = (
        Team.objects.filter(
            Q(school__icontains=query)
            | Q(mascot__icontains=query)
            | Q(alternative_names__name__icontains=query)
        )
        .distinct()
        [:10]
    )
    results = [{"id": team.id, "name": str(team)} for team in teams]
    return JsonResponse({"results": results})


def team_detail(request, pk: int):
    team = get_object_or_404(Team.objects.prefetch_related("logos", "location"), pk=pk)
    logos = list(team.logos.values_list("url", flat=True))
    matches_qs = (
        Match.objects.filter(Q(home_team=team) | Q(away_team=team))
        .select_related("home_team", "away_team", "venue")
        [:5]
    )
    matches = []
    for match in matches_qs:
        if match.home_team_id == team.id:
            opponent = match.away_team.school
            team_score, opp_score = match.home_score, match.away_score
        else:
            opponent = match.home_team.school
            team_score, opp_score = match.away_score, match.home_score
        if (
            match.completed
            and team_score is not None
            and opp_score is not None
        ):
            if team_score > opp_score:
                result = "W"
            elif team_score < opp_score:
                result = "L"
            else:
                result = "T"
        else:
            result = ""
        try:
            url = reverse("admin:core_match_change", args=[match.pk])
        except NoReverseMatch:
            url = ""
        matches.append(
            {
                "id": match.pk,
                "opponent": opponent,
                "date": match.start_date.strftime("%Y-%m-%d"),
                "result": result,
                "venue": match.venue.name if match.venue else "",
                "url": url,
            }
        )
    data = {
        "id": team.pk,
        "school": team.school,
        "mascot": team.mascot or "",
        "abbreviation": team.abbreviation or "",
        "classification": team.get_classification_display() if team.classification else "",
        "color": team.color,
        "alternate_color": team.alternate_color,
        "twitter": team.twitter or "",
        "location": team.location.name if team.location else "",
        "logos": logos,
        "matches": matches,
    }
    return JsonResponse(data)


def _get_admin_urls(urls):
    def get_urls():
        custom_urls = [
            path("team-info/", admin.site.admin_view(team_info_page), name="team-info"),
            path(
                "team-info/search/",
                admin.site.admin_view(team_search),
                name="team-info-search",
            ),
            path(
                "team-info/<int:pk>/",
                admin.site.admin_view(team_detail),
                name="team-info-detail",
            ),
        ]
        return custom_urls + urls()

    return get_urls


admin.site.get_urls = _get_admin_urls(admin.site.get_urls)
