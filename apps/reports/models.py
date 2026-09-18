"""Async report generation (CSV / Excel / PDF)."""
from django.conf import settings
from django.db import models

from apps.common.models import UUIDTimeStampedModel


class ReportJob(UUIDTimeStampedModel):
    class Kind(models.TextChoices):
        FINANCIAL = "financial", "Financial"
        USERS = "users", "Users"
        OFFERS = "offers", "Offers"
        CPA = "cpa", "CPA networks"
        WITHDRAWALS = "withdrawals", "Withdrawals"
        FRAUD = "fraud", "Fraud"
        GAMES = "games", "Games"
        SURVEYS = "surveys", "Surveys"

    class Status(models.TextChoices):
        QUEUED = "queued", "Queued"
        RUNNING = "running", "Running"
        READY = "ready", "Ready"
        FAILED = "failed", "Failed"
        EXPIRED = "expired", "Expired"

    kind = models.CharField(max_length=32, choices=Kind.choices, db_index=True)
    format = models.CharField(max_length=8, default="csv")
    params = models.JSONField(default=dict, blank=True)
    status = models.CharField(
        max_length=16, choices=Status.choices, default=Status.QUEUED, db_index=True
    )
    file = models.FileField(upload_to="reports/", null=True, blank=True)
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="report_jobs",
    )
    error = models.CharField(max_length=255, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"report:{self.kind}:{self.status}"
