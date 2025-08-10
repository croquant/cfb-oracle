"""Admin configuration for conference model."""

from django.contrib import admin
from unfold.admin import ModelAdmin

from core.models.conference import Conference


@admin.register(Conference)
class ConferenceAdmin(ModelAdmin):
    """Admin configuration for the Conference model."""

    list_display = ("name", "short_name", "abbreviation", "classification")
    list_filter = ("classification",)
    search_fields = ("name", "short_name", "abbreviation")
    list_filter_sheet = False
    prepopulated_fields = {"slug": ("name",)}
