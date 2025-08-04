from django.contrib import admin
from django.core.paginator import Paginator
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
    team = get_object_or_404(
        Team.objects.prefetch_related("logos", "location"), pk=pk
    )
    logos = list(team.logos.values_list("url", flat=True))

    upcoming_qs = (
        Match.objects.filter(
            Q(home_team=team) | Q(away_team=team), completed=False
        )
        .select_related("home_team", "away_team", "venue")
        .prefetch_related("home_team__logos", "away_team__logos")
        .order_by("start_date")[:5]
    )
    upcoming_matches = []
    for match in upcoming_qs:
        def get_logo(tm):
            logo = tm.logos.first()
            return logo.url if logo else ""

        try:
            url = reverse("admin:core_match_change", args=[match.pk])
        except NoReverseMatch:
            url = ""

        upcoming_matches.append(
            {
                "id": match.pk,
                "home": {
                    "name": match.home_team.school,
                    "logo": get_logo(match.home_team),
                },
                "away": {
                    "name": match.away_team.school,
                    "logo": get_logo(match.away_team),
                },
                "is_home": match.home_team_id == team.id,
                "date": match.start_date.strftime("%Y-%m-%d %H:%M"),
                "venue": match.venue.name if match.venue else "",
                "url": url,
            }
        )

    data = {
        "id": team.pk,
        "school": team.school,
        "mascot": team.mascot or "",
        "abbreviation": team.abbreviation or "",
        "classification": team.get_classification_display()
        if team.classification
        else "",
        "color": team.color,
        "alternate_color": team.alternate_color,
        "twitter": team.twitter or "",
        "location": team.location.name if team.location else "",
        "logos": logos,
        "upcoming_matches": upcoming_matches,
    }
    return JsonResponse(data)


def team_completed_matches(request, pk: int):
    team = get_object_or_404(Team, pk=pk)
    page = int(request.GET.get("page", 1))
    matches_qs = (
        Match.objects.filter(Q(home_team=team) | Q(away_team=team), completed=True)
        .select_related("home_team", "away_team", "venue")
        .prefetch_related("home_team__logos", "away_team__logos")
    )
    paginator = Paginator(matches_qs, 5)
    page_obj = paginator.get_page(page)

    matches = []
    for match in page_obj.object_list:
        def get_logo(tm):
            logo = tm.logos.first()
            return logo.url if logo else ""

        if match.home_team_id == team.id:
            opponent = match.away_team.school
            opponent_logo = get_logo(match.away_team)
            team_logo = get_logo(match.home_team)
            team_score, opp_score = match.home_score, match.away_score
        else:
            opponent = match.home_team.school
            opponent_logo = get_logo(match.home_team)
            team_logo = get_logo(match.away_team)
            team_score, opp_score = match.away_score, match.home_score

        if team_score is not None and opp_score is not None:
            if team_score > opp_score:
                result = "W"
                result_class = "text-green-600"
            elif team_score < opp_score:
                result = "L"
                result_class = "text-red-600"
            else:
                result = "T"
                result_class = "text-gray-600"
        else:
            result = ""
            result_class = "text-gray-600"

        try:
            url = reverse("admin:core_match_change", args=[match.pk])
        except NoReverseMatch:
            url = ""

        matches.append(
            {
                "id": match.pk,
                "opponent": opponent,
                "team_logo": team_logo,
                "opponent_logo": opponent_logo,
                "team_score": team_score,
                "opponent_score": opp_score,
                "date": match.start_date.strftime("%Y-%m-%d"),
                "attendance": match.attendance,
                "result": result,
                "result_class": result_class,
                "venue": match.venue.name if match.venue else "",
                "url": url,
            }
        )

    context = {
        "matches": matches,
        "team_id": team.id,
        "next_page": page_obj.next_page_number() if page_obj.has_next() else None,
    }
    return render(request, "admin/team_completed_matches.html", context)


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
            path(
                "team-info/<int:pk>/results/",
                admin.site.admin_view(team_completed_matches),
                name="team-info-results",
            ),
        ]
        return custom_urls + urls()

    return get_urls


admin.site.get_urls = _get_admin_urls(admin.site.get_urls)
