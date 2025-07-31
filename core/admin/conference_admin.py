from django.contrib import admin
from unfold.admin import ModelAdmin

from core.models.conference import Conference


@admin.register(Conference)
class ConferenceAdmin(ModelAdmin):
    list_display = ("name", "short_name", "abbreviation", "classification")
    list_filter = ("classification",)
    search_fields = ("name", "short_name", "abbreviation")
    list_filter_sheet = False
    fieldsets = (
        (
            "General",
            {
                "fields": (
                    ("name", "short_name"),
                    ("abbreviation", "classification"),
                ),
                "classes": ("tab",),
            },
        ),
    )
