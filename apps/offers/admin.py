"""Admin registrations for the offers module.

Generic registrations; add list_display/filters per model as the admin UX
is built out (docs/DRD.md §57, §164).
"""
from django.contrib import admin

from . import models



@admin.register(models.OfferCategory)
class OfferCategoryAdmin(admin.ModelAdmin):
    list_per_page = 50
    show_full_result_count = False


@admin.register(models.Offer)
class OfferAdmin(admin.ModelAdmin):
    list_per_page = 50
    show_full_result_count = False


@admin.register(models.CampaignQuota)
class CampaignQuotaAdmin(admin.ModelAdmin):
    list_per_page = 50
    show_full_result_count = False


@admin.register(models.OfferClick)
class OfferClickAdmin(admin.ModelAdmin):
    list_per_page = 50
    show_full_result_count = False


@admin.register(models.OfferConversion)
class OfferConversionAdmin(admin.ModelAdmin):
    list_per_page = 50
    show_full_result_count = False


@admin.register(models.OfferPostback)
class OfferPostbackAdmin(admin.ModelAdmin):
    list_per_page = 50
    show_full_result_count = False
