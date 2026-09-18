"""Admin registrations for the notifications module.

Generic registrations; add list_display/filters per model as the admin UX
is built out (docs/DRD.md §57, §164).
"""
from django.contrib import admin

from . import models



@admin.register(models.Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_per_page = 50
    show_full_result_count = False


@admin.register(models.EmailTemplate)
class EmailTemplateAdmin(admin.ModelAdmin):
    list_per_page = 50
    show_full_result_count = False


@admin.register(models.SMSLog)
class SMSLogAdmin(admin.ModelAdmin):
    list_per_page = 50
    show_full_result_count = False
