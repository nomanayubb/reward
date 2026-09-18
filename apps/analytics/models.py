"""Analytics: daily aggregates and a high-volume event stream.

Keep high-volume events out of the transactional tables (docs/DRD.md §174).
As volume grows this can be piped to ClickHouse/BigQuery without touching
the financial schema.
"""
from django.conf import settings
from django.db import models

from apps.common.models import TimeStampedModel, UUIDTimeStampedModel


class DailyStatistic(TimeStampedModel):
    date = models.DateField(db_index=True)
    key = models.CharField(max_length=64, db_index=True)
    value = models.DecimalField(max_digits=24, decimal_places=8, default=0)
    dimension = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-date", "key"]
        constraints = [
            models.UniqueConstraint(fields=["date", "key"], name="uniq_daily_stat_key")
        ]

    def __str__(self):
        return f"{self.date}:{self.key}={self.value}"


class AnalyticsEvent(UUIDTimeStampedModel):
    name = models.CharField(max_length=64, db_index=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="analytics_events",
    )
    session_key = models.CharField(max_length=64, blank=True)
    payload = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["name", "created_at"])]

    def __str__(self):
        return f"event:{self.name}"
