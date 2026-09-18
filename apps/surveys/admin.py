"""Admin registrations for the surveys module.

Generic registrations; add list_display/filters per model as the admin UX
is built out (docs/DRD.md §57, §164).
"""
from django.contrib import admin

from . import models



@admin.register(models.SurveyProvider)
class SurveyProviderAdmin(admin.ModelAdmin):
    list_per_page = 50
    show_full_result_count = False


@admin.register(models.Survey)
class SurveyAdmin(admin.ModelAdmin):
    list_per_page = 50
    show_full_result_count = False


@admin.register(models.SurveySession)
class SurveySessionAdmin(admin.ModelAdmin):
    list_per_page = 50
    show_full_result_count = False


@admin.register(models.SurveyCompletion)
class SurveyCompletionAdmin(admin.ModelAdmin):
    list_per_page = 50
    show_full_result_count = False
