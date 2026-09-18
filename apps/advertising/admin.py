"""Admin registrations for the advertising module.

Generic registrations; add list_display/filters per model as the admin UX
is built out (docs/DRD.md §57, §164).
"""
from django.contrib import admin

from . import models



@admin.register(models.AdProvider)
class AdProviderAdmin(admin.ModelAdmin):
    list_per_page = 50
    show_full_result_count = False


@admin.register(models.AdPlacement)
class AdPlacementAdmin(admin.ModelAdmin):
    list_per_page = 50
    show_full_result_count = False


@admin.register(models.AdCampaign)
class AdCampaignAdmin(admin.ModelAdmin):
    list_per_page = 50
    show_full_result_count = False


@admin.register(models.AdImpression)
class AdImpressionAdmin(admin.ModelAdmin):
    list_per_page = 50
    show_full_result_count = False


@admin.register(models.AdClick)
class AdClickAdmin(admin.ModelAdmin):
    list_per_page = 50
    show_full_result_count = False
