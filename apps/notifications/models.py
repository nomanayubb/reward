"""Notifications: in-app, email and SMS delivery records + templates."""
from django.conf import settings
from django.db import models

from apps.common.models import TimeStampedModel, UUIDTimeStampedModel


class Notification(UUIDTimeStampedModel):
    class Channel(models.TextChoices):
        IN_APP = "in_app", "In-app"
        EMAIL = "email", "Email"
        SMS = "sms", "SMS"
        PUSH = "push", "Push"

    class Kind(models.TextChoices):
        SYSTEM = "system", "System"
        REWARD = "reward", "Reward"
        WITHDRAWAL = "withdrawal", "Withdrawal"
        DEPOSIT = "deposit", "Deposit"
        SECURITY = "security", "Security"
        PROMO = "promo", "Promotion"
        BONUS = "bonus", "Bonus"
        SUPPORT = "support", "Support"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications"
    )
    kind = models.CharField(max_length=16, choices=Kind.choices, default=Kind.SYSTEM, db_index=True)
    channel = models.CharField(
        max_length=16, choices=Channel.choices, default=Channel.IN_APP, db_index=True
    )
    title = models.CharField(max_length=160)
    body = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    is_read = models.BooleanField(default=False, db_index=True)
    read_at = models.DateTimeField(null=True, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    delivery_status = models.CharField(max_length=32, blank=True)
    delivery_error = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["user", "is_read", "created_at"])]

    def __str__(self):
        return f"notification:{self.user_id}:{self.title[:40]}"


class EmailTemplate(UUIDTimeStampedModel):
    code = models.CharField(max_length=64, unique=True, help_text="e.g. welcome, withdrawal_approved")
    name = models.CharField(max_length=120)
    subject = models.CharField(max_length=255)
    html_body = models.TextField(blank=True)
    text_body = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["code"]

    def __str__(self):
        return f"{self.name} ({self.code})"


class SMSLog(TimeStampedModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="sms_logs",
    )
    phone = models.CharField(max_length=32)
    message = models.TextField()
    provider = models.CharField(max_length=64, blank=True)
    status = models.CharField(max_length=32, blank=True)
    provider_response = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"sms:{self.phone}:{self.status}"
