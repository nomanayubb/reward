"""Admin registrations for the games module.

Generic registrations; add list_display/filters per model as the admin UX
is built out (docs/DRD.md §57, §164).
"""
from django.contrib import admin

from . import models



@admin.register(models.GameCategory)
class GameCategoryAdmin(admin.ModelAdmin):
    list_per_page = 50
    show_full_result_count = False


@admin.register(models.Game)
class GameAdmin(admin.ModelAdmin):
    list_per_page = 50
    show_full_result_count = False


@admin.register(models.GameRewardRule)
class GameRewardRuleAdmin(admin.ModelAdmin):
    list_per_page = 50
    show_full_result_count = False


@admin.register(models.GameSession)
class GameSessionAdmin(admin.ModelAdmin):
    list_per_page = 50
    show_full_result_count = False


@admin.register(models.GameEvent)
class GameEventAdmin(admin.ModelAdmin):
    list_per_page = 50
    show_full_result_count = False
