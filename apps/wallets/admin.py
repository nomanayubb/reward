"""Admin registrations for the wallets module.

Generic registrations; add list_display/filters per model as the admin UX
is built out (docs/DRD.md §57, §164).
"""
from django.contrib import admin

from . import models


@admin.register(models.Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_per_page = 50
    show_full_result_count = False


@admin.register(models.WalletAccount)
class WalletAccountAdmin(admin.ModelAdmin):
    list_per_page = 50
    show_full_result_count = False


@admin.register(models.BalanceSnapshot)
class BalanceSnapshotAdmin(admin.ModelAdmin):
    list_per_page = 50
    show_full_result_count = False
