"""Surveys: providers, survey catalog, sessions and completions.

Provider-specific behaviour lives behind adapters (``apps/surveys/providers/``).
The survey flow follows docs/DRD.md §13: fetch -> eligibility -> risk filter ->
start -> provider completion -> postback -> verification -> pending reward ->
approval -> wallet credit.
"""
from django.conf import settings
from django.db import models

from apps.common.fields import money_field
from apps.common.models import TimeStampedModel, UUIDTimeStampedModel


class SurveyProvider(UUIDTimeStampedModel):
    class Health(models.TextChoices):
        HEALTHY = "healthy", "Healthy"
        DEGRADED = "degraded", "Degraded"
        DOWN = "down", "Down"
        UNKNOWN = "unknown", "Unknown"

    code = models.CharField(max_length=64, unique=True)
    name = models.CharField(max_length=120)
    adapter_path = models.CharField(
        max_length=255,
        help_text="Dotted path to the adapter class, e.g. apps.surveys.providers.example.ExampleProvider",
    )
    is_enabled = models.BooleanField(default=False, db_index=True)
    priority = models.PositiveIntegerField(default=100)
    config = models.JSONField(default=dict, blank=True)

    health = models.CharField(max_length=16, choices=Health.choices, default=Health.UNKNOWN)
    last_sync_at = models.DateTimeField(null=True, blank=True)
    last_error = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["priority", "name"]

    def __str__(self):
        return f"{self.name} ({self.code})"


class Survey(UUIDTimeStampedModel):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        PAUSED = "paused", "Paused"
        EXPIRED = "expired", "Expired"
        PAUSED_BY_QUOTA = "paused_by_quota", "Paused by quota"

    provider = models.ForeignKey(
        SurveyProvider, on_delete=models.CASCADE, related_name="surveys"
    )
    external_id = models.CharField(max_length=191, db_index=True)

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=64, blank=True)
    country = models.CharField(max_length=2, blank=True, db_index=True)
    language = models.CharField(max_length=8, blank=True)
    device = models.CharField(max_length=16, blank=True)

    estimated_minutes = models.PositiveIntegerField(default=0)
    payout = money_field(help_text="Provider payout (revenue).")
    user_reward = money_field(help_text="What the user receives.")
    currency = models.CharField(max_length=8, default="USD")
    reward_mode = models.CharField(max_length=16, default="cash")

    qualification_rate = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )
    status = models.CharField(
        max_length=24, choices=Status.choices, default=Status.ACTIVE, db_index=True
    )
    daily_cap = models.PositiveIntegerField(null=True, blank=True)
    user_cap = models.PositiveIntegerField(default=1)
    expires_at = models.DateTimeField(null=True, blank=True)

    raw_payload = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-payout"]
        constraints = [
            models.UniqueConstraint(
                fields=["provider", "external_id"], name="uniq_survey_provider_external"
            )
        ]
        indexes = [models.Index(fields=["status", "country"])]

    def __str__(self):
        return f"survey:{self.title[:40]}"


class SurveySession(UUIDTimeStampedModel):
    class Status(models.TextChoices):
        STARTED = "started", "Started"
        COMPLETED = "completed", "Completed"
        DISQUALIFIED = "disqualified", "Disqualified"
        ABANDONED = "abandoned", "Abandoned"
        INVALIDATED = "invalidated", "Invalidated"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="survey_sessions"
    )
    survey = models.ForeignKey(Survey, on_delete=models.PROTECT, related_name="sessions")
    status = models.CharField(
        max_length=16, choices=Status.choices, default=Status.STARTED, db_index=True
    )
    started_at = models.DateTimeField(auto_now_add=True, db_index=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        ordering = ["-started_at"]
        indexes = [models.Index(fields=["user", "survey", "status"])]

    def __str__(self):
        return f"survey-session:{self.survey_id}:{self.user_id}"


class SurveyCompletion(UUIDTimeStampedModel):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"
        REVERSED = "reversed", "Reversed"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="survey_completions"
    )
    survey = models.ForeignKey(Survey, on_delete=models.PROTECT, related_name="completions")
    session = models.ForeignKey(
        SurveySession, null=True, blank=True, on_delete=models.SET_NULL, related_name="completions"
    )
    provider = models.ForeignKey(
        SurveyProvider, on_delete=models.PROTECT, related_name="completions"
    )
    external_completion_id = models.CharField(max_length=191)

    payout = money_field()
    user_reward = money_field()
    status = models.CharField(
        max_length=16, choices=Status.choices, default=Status.PENDING, db_index=True
    )
    reward = models.ForeignKey(
        "rewards.Reward", null=True, blank=True, on_delete=models.SET_NULL, related_name="survey_completions"
    )
    raw_payload = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["provider", "external_completion_id"],
                name="uniq_survey_completion_external",
            )
        ]

    def __str__(self):
        return f"completion:{self.external_completion_id}:{self.status}"
