from django.contrib import admin
from unfold.admin import ModelAdmin

from core.models.venue import Venue


@admin.register(Venue)
class VenueAdmin(ModelAdmin):
    pass
