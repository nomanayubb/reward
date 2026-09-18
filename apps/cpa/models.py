"""CPA provider registry and health.

Each provider row points at an adapter class implementing the provider
interface (get_offers / track_click / process_postback / validate_conversion /
get_campaign_status / get_reporting_data). Adding a network = new adapter +
row + credentials, never a rewrite.
"""
from django.db import models

from apps.common.models import UUIDTimeStampedModel


class CPAProvider(UUIDTimeStampedModel):
    class Health(models.TextChoices):
        HEALTHY = "healthy", "Healthy"
        DEGRADED = "degraded", "Degraded"
        DOWN = "down", "Down"
        UNKNOWN = "unknown", "Unknown"

    code = models.CharField(max_length=64, unique=True, help_text="e.g. network_a")
    name = models.CharField(max_length=120)
    adapter_path = models.CharField(
        max_length=255,
        help_text="Dotted path, e.g. apps.cpa.providers.network_a.NetworkAAdapter",
    )
    is_enabled = models.BooleanField(default=False, db_index=True)
    priority = models.PositiveIntegerField(default=100)

    supports_api_sync = models.BooleanField(default=False)
    supports_postback = models.BooleanField(default=True)
    supports_signature = models.BooleanField(default=True)

    config = models.JSONField(default=dict, blank=True)
    health = models.CharField(max_length=16, choices=Health.choices, default=Health.UNKNOWN)
    last_sync_at = models.DateTimeField(null=True, blank=True)
    last_error = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["priority", "name"]

    def __str__(self):
        return f"{self.name} ({self.code})"


class CPAProviderHealthLog(UUIDTimeStampedModel):
    provider = models.ForeignKey(CPAProvider, on_delete=models.CASCADE, related_name="health_logs")
    status = models.CharField(max_length=16, choices=CPAProvider.Health.choices)
    latency_ms = models.PositiveIntegerField(null=True, blank=True)
    detail = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"health:{self.provider_id}:{self.status}"
