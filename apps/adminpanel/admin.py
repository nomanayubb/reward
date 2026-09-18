"""Admin registrations for the adminpanel module.

Generic registrations; add list_display/filters per model as the admin UX
is built out (docs/DRD.md §57, §164).
"""
from django.contrib import admin

from . import models


@admin.register(models.Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_per_page = 50
    show_full_result_count = False


@admin.register(models.Role)
class RoleAdmin(admin.ModelAdmin):
    list_per_page = 50
    show_full_result_count = False


@admin.register(models.PlatformSetting)
class PlatformSettingAdmin(admin.ModelAdmin):
    list_per_page = 50
    show_full_result_count = False


@admin.register(models.ConfigurationVersion)
class ConfigurationVersionAdmin(admin.ModelAdmin):
    list_per_page = 50
    show_full_result_count = False


@admin.register(models.FeatureFlag)
class FeatureFlagAdmin(admin.ModelAdmin):
    list_per_page = 50
    show_full_result_count = False


@admin.register(models.AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_per_page = 50
    show_full_result_count = False
