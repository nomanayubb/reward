"""Admin registrations for the users module.

Generic registrations; add list_display/filters per model as the admin UX
is built out (docs/DRD.md §57, §164).
"""
from django.contrib import admin

from . import models



@admin.register(models.UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_per_page = 50
    show_full_result_count = False


@admin.register(models.UserSecurity)
class UserSecurityAdmin(admin.ModelAdmin):
    list_per_page = 50
    show_full_result_count = False


@admin.register(models.UserDevice)
class UserDeviceAdmin(admin.ModelAdmin):
    list_per_page = 50
    show_full_result_count = False


@admin.register(models.UserSession)
class UserSessionAdmin(admin.ModelAdmin):
    list_per_page = 50
    show_full_result_count = False


@admin.register(models.UserRiskProfile)
class UserRiskProfileAdmin(admin.ModelAdmin):
    list_per_page = 50
    show_full_result_count = False


@admin.register(models.UserRestriction)
class UserRestrictionAdmin(admin.ModelAdmin):
    list_per_page = 50
    show_full_result_count = False
