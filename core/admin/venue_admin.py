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
    fieldsets = (
        (
            "General",
            {
                "fields": (
                    "name",
                    ("city", "state"),
                    ("zip_code", "country_code"),
                    ("capacity", "construction_year"),
                ),
                "classes": ("tab",),
            },
        ),
        (
            "Location",
            {
                "fields": (
                    "timezone",
                    ("latitude", "longitude"),
                    "elevation",
                    ("grass", "dome"),
                ),
                "classes": ("tab",),
            },
        ),
    )
