"""Risk scoring rules and score history.

Actions the engine may take: allow, rate-limit, hold reward, require
verification, disable offers, disable withdrawals, freeze account, alert admin.
"""
from django.conf import settings
from django.db import models

from apps.common.models import UUIDTimeStampedModel


class RiskRule(UUIDTimeStampedModel):
    class Action(models.TextChoices):
        ALLOW = "allow", "Allow"
        RATE_LIMIT = "rate_limit", "Rate limit"
        HOLD_REWARD = "hold_reward", "Hold reward"
        REQUIRE_VERIFICATION = "require_verification", "Require verification"
        DISABLE_OFFERS = "disable_offers", "Disable offers"
        DISABLE_WITHDRAWALS = "disable_withdrawals", "Disable withdrawals"
        FREEZE_ACCOUNT = "freeze_account", "Freeze account"
        ALERT_ADMIN = "alert_admin", "Alert admin"

    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True, db_index=True)
    priority = models.PositiveIntegerField(default=100)

    conditions = models.JSONField(
        default=dict, blank=True,
        help_text='e.g. {"min_score": 50, "account_age_days_lt": 3}',
    )
    action = models.CharField(max_length=32, choices=Action.choices, default=Action.ALERT_ADMIN)
    score_delta = models.SmallIntegerField(
        default=0, help_text="Applied to the user's risk score when the rule matches."
    )

    class Meta:
        ordering = ["priority", "name"]

    def __str__(self):
        return self.name


class RiskScore(UUIDTimeStampedModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="risk_scores"
    )
    score = models.PositiveSmallIntegerField()
    reasons = models.JSONField(default=list, blank=True)
    computed_at = models.DateTimeField(auto_now_add=True, db_index=True)
    source = models.CharField(max_length=64, blank=True)

    class Meta:
        ordering = ["-computed_at"]
        indexes = [models.Index(fields=["user", "computed_at"])]

    def __str__(self):
        return f"score:{self.user_id}:{self.score}"
