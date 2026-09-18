"""Admin registrations for the accounts module."""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from . import models


@admin.register(models.User)
class UserAdmin(BaseUserAdmin):
    ordering = ("-date_joined",)
    list_display = ("email", "username", "status", "country", "is_staff", "date_joined")
    list_filter = ("status", "is_staff", "is_superuser", "is_email_verified", "country")
    search_fields = ("email", "username", "phone", "referral_code")
    readonly_fields = ("date_joined", "last_login", "last_seen_at", "last_login_ip")

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Profile", {"fields": ("username", "phone", "country", "referral_code")}),
        (
            "Status",
            {"fields": ("status", "is_active", "is_staff", "is_superuser")},
        ),
        (
            "Verification",
            {"fields": ("is_email_verified", "is_phone_verified", "email_verified_at", "phone_verified_at")},
        ),
        ("Activity", {"fields": ("date_joined", "last_login", "last_seen_at", "last_login_ip")}),
        ("Permissions", {"fields": ("groups", "user_permissions")}),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "password1", "password2", "is_staff", "is_superuser"),
            },
        ),
    )
