from django.contrib import admin
from django.templatetags.static import static
from django.utils.html import format_html
from unfold.admin import ModelAdmin, TabularInline

from core.forms import TeamForm

from core.models.team import Team, TeamAlternativeName, TeamLogo


class TeamAlternativeNameTabularInline(TabularInline):
    model = TeamAlternativeName
    fields = ("name",)
    extra = 0
    hide_title = True
    tab = True


class TeamLogoInline(TabularInline):
    model = TeamLogo
    fields = ("url", "preview")
    readonly_fields = ("preview",)
    extra = 0
    hide_title = True
    tab = True

    def preview(self, obj):
        if obj.url:
            return format_html(f'<img src="{obj.url}" class="h-16" />')
        placeholder_url = static("images/logo_placeholder.png")
        return format_html(f'<img src="{placeholder_url}" class="h-16" />')

    preview.short_description = "Logo"


@admin.register(Team)
class TeamAdmin(ModelAdmin):
    form = TeamForm
    search_fields = ("school", "mascot")
    list_display = (
        "logo_display",
        "school",
        "mascot",
        "abbreviation",
        "conference",
    )
    list_select_related = ("location", "conference")
    list_filter = (
        "classification",
        "conference",
    )
    list_filter_sheet = False
    prepopulated_fields = {"slug": ("school",)}
    inlines = [TeamAlternativeNameTabularInline, TeamLogoInline]
    fieldsets = (
        (
            None,
            {
                "fields": (
                    ("school", "mascot"),
                    ("slug", "abbreviation"),
                    ("classification", "conference"),
                    ("color", "alternate_color"),
                    "twitter",
                    "location",
                ),
            },
        ),
    )

    def logo_display(self, obj):
        logo = obj.logos.first()
        if logo:
            return format_html(f'<img src="{logo.url}" class="h-8" />')

    logo_display.short_description = "Logo"
