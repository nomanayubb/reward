"""Admin registrations for the cms module.

Generic registrations; add list_display/filters per model as the admin UX
is built out (docs/DRD.md §57, §164).
"""
from django.contrib import admin

from . import models



@admin.register(models.CMSPage)
class CMSPageAdmin(admin.ModelAdmin):
    list_per_page = 50
    show_full_result_count = False


@admin.register(models.PageVersion)
class PageVersionAdmin(admin.ModelAdmin):
    list_per_page = 50
    show_full_result_count = False


@admin.register(models.BlogCategory)
class BlogCategoryAdmin(admin.ModelAdmin):
    list_per_page = 50
    show_full_result_count = False


@admin.register(models.BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_per_page = 50
    show_full_result_count = False
