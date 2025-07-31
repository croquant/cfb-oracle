from django.contrib import admin
from django.utils.html import format_html
from unfold.admin import ModelAdmin, TabularInline

from core.models.team import Team, TeamAlternativeName, TeamLogo


class TeamAlternativeNameTabularInline(TabularInline):
    model = TeamAlternativeName
    fields = ("name",)
    extra = 0
    hide_title = True


class TeamLogoInline(TabularInline):
    model = TeamLogo
    fields = ("url", "preview")
    readonly_fields = ("preview",)
    extra = 0

    def preview(self, obj):
        if obj.url:
            return format_html(
                '<img src="{}" class="h-8" />',
                obj.url,
            )
        return format_html(
            '<span class="material-symbols-outlined text-base-400">image</span>'
        )

    preview.short_description = "Logo"


@admin.register(Team)
class TeamAdmin(ModelAdmin):
    search_fields = ("school", "mascot")
    list_display = (
        "logo_display",
        "school",
        "mascot",
        "abbreviation",
        "conference",
    )
    list_filter = (
        "classification",
        "conference",
    )
    list_filter_sheet = False
    readonly_fields = ("logo_display",)
    inlines = [TeamAlternativeNameTabularInline, TeamLogoInline]

    def logo_display(self, obj):
        logo = obj.logos.first()
        if logo:
            return format_html('<img src="{}" class="h-8" />', logo.url)
        return format_html('<span class="material-symbols-outlined text-base-400">image</span>')

    logo_display.short_description = "Logo"

