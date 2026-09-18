"""Admin panel core: RBAC, runtime platform settings, feature flags,
configuration versioning and the immutable audit log.

This is the module that makes the platform configurable without code changes:
``PlatformSetting`` values are read through ``apps.adminpanel.settings.get_setting``
and fall back to ``settings.PLATFORM_DEFAULTS``.
"""
from django.conf import settings
from django.db import models

from apps.common.models import TimeStampedModel, UUIDTimeStampedModel


class Permission(UUIDTimeStampedModel):
    code = models.CharField(max_length=128, unique=True, help_text="e.g. withdrawals.approve")
    name = models.CharField(max_length=160)
    group = models.CharField(max_length=64, blank=True, db_index=True)

    class Meta:
        ordering = ["group", "code"]

    def __str__(self):
        return self.code


class Role(UUIDTimeStampedModel):
    name = models.CharField(max_length=80, unique=True)
    description = models.CharField(max_length=255, blank=True)
    permissions = models.ManyToManyField(Permission, blank=True, related_name="roles")
    users = models.ManyToManyField(
        settings.AUTH_USER_MODEL, blank=True, related_name="admin_roles"
    )
    is_system = models.BooleanField(
        default=False, help_text="System roles cannot be deleted."
    )

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class PlatformSetting(UUIDTimeStampedModel):
    """Runtime configuration (points conversion, limits, fees, ...)."""

    key = models.CharField(max_length=128, unique=True)
    value = models.JSONField(default=dict, blank=True)
    value_type = models.CharField(
        max_length=16, default="json",
        help_text="str / int / decimal / bool / json — used for admin form rendering.",
    )
    group = models.CharField(max_length=64, default="general", db_index=True)
    description = models.CharField(max_length=255, blank=True)
    is_public = models.BooleanField(default=False, help_text="Exposed to the frontend.")
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="settings_updated",
    )

    class Meta:
        ordering = ["group", "key"]

    def __str__(self):
        return self.key


class ConfigurationVersion(UUIDTimeStampedModel):
    """History of configuration changes with rollback support."""

    key = models.CharField(max_length=191, db_index=True)
    old_value = models.JSONField(null=True, blank=True)
    new_value = models.JSONField(null=True, blank=True)
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="config_versions",
    )
    note = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["key", "created_at"])]

    def __str__(self):
        return f"{self.key} @ {self.created_at}"


class FeatureFlag(UUIDTimeStampedModel):
    key = models.CharField(max_length=64, unique=True, help_text="e.g. FEATURE_GAMES")
    name = models.CharField(max_length=120, blank=True)
    is_enabled = models.BooleanField(default=False, db_index=True)
    rollout_percent = models.PositiveSmallIntegerField(default=100)
    description = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["key"]

    def __str__(self):
        return f"{self.key}:{'on' if self.is_enabled else 'off'}"


class AuditLog(TimeStampedModel):
    """Every sensitive admin action, immutable by convention and policy."""

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="audit_logs",
    )
    action = models.CharField(max_length=128, db_index=True)
    object_type = models.CharField(max_length=128, blank=True, db_index=True)
    object_id = models.CharField(max_length=128, blank=True, db_index=True)
    old_value = models.JSONField(null=True, blank=True)
    new_value = models.JSONField(null=True, blank=True)
    reason = models.CharField(max_length=255, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["object_type", "object_id", "created_at"])]

    def __str__(self):
        return f"audit:{self.action}:{self.object_type}:{self.object_id}"

    def save(self, *args, **kwargs):
        if not self._state.adding:
            from django.core.exceptions import ValidationError

            raise ValidationError("Audit log entries are immutable.")
        super().save(*args, **kwargs)
