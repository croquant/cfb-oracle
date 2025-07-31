from django.contrib import admin
from unfold.admin import ModelAdmin

from core.models.venue import Venue


@admin.register(Venue)
class VenueAdmin(ModelAdmin):
    list_display = (
        "name",
        "city",
        "state",
        "capacity",
        "construction_year",
    )
    list_filter = (
        "grass",
        "dome",
        "country_code",
    )
    list_filter_sheet = False
    search_fields = ("name", "city", "state")
