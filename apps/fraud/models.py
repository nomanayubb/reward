"""Fraud detection: signals, events and automated actions.

Detection uses transparent rules first (VPN/proxy/TOR, emulator, multi-account,
device/IP reuse, impossible completion times, rapid conversions, postback
abuse). Never auto-ban on a single signal — combine risk score + evidence.
"""
from django.conf import settings
from django.db import models

from apps.common.models import UUIDTimeStampedModel


class FraudEvent(UUIDTimeStampedModel):
    class Kind(models.TextChoices):
        VPN = "vpn", "VPN detected"
        PROXY = "proxy", "Proxy detected"
        TOR = "tor", "TOR exit node"
        EMULATOR = "emulator", "Emulator"
        MULTI_ACCOUNT = "multi_account", "Multiple accounts"
        DEVICE_REUSE = "device_reuse", "Device reuse"
        IP_REUSE = "ip_reuse", "IP reuse"
        COOKIE_MANIPULATION = "cookie_manipulation", "Cookie manipulation"
        FAKE_POSTBACK = "fake_postback", "Fake postback"
        RAPID_CONVERSION = "rapid_conversion", "Rapid conversions"
        IMPOSSIBLE_TIME = "impossible_time", "Impossible completion time"
        REPEATED_INSTALL = "repeated_install", "Repeated app install"
        CHARGEBACK = "chargeback", "Chargeback"
        PAYMENT_ABUSE = "payment_abuse", "Payment abuse"
        REFERRAL_ABUSE = "referral_abuse", "Referral abuse"

    class Severity(models.TextChoices):
        LOW = "low", "Low"
        MEDIUM = "medium", "Medium"
        HIGH = "high", "High"
        CRITICAL = "critical", "Critical"

    class Status(models.TextChoices):
        OPEN = "open", "Open"
        REVIEWING = "reviewing", "Reviewing"
        RESOLVED = "resolved", "Resolved"
        FALSE_POSITIVE = "false_positive", "False positive"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="fraud_events",
    )
    kind = models.CharField(max_length=32, choices=Kind.choices, db_index=True)
    severity = models.CharField(
        max_length=16, choices=Severity.choices, default=Severity.LOW, db_index=True
    )
    status = models.CharField(
        max_length=16, choices=Status.choices, default=Status.OPEN, db_index=True
    )

    evidence = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    device_id_hash = models.CharField(max_length=128, blank=True)
    action_taken = models.CharField(max_length=64, blank=True)
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="fraud_events_resolved",
    )
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolution_note = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "status"]),
            models.Index(fields=["kind", "severity", "created_at"]),
        ]

    def __str__(self):
        return f"fraud:{self.kind}:{self.severity}"
