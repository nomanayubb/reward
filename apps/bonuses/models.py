"""Bonus engine: configurable rules, issued bonuses and claims."""
from django.conf import settings
from django.db import models

from apps.common.fields import money_field
from apps.common.models import UUIDTimeStampedModel


class BonusRule(UUIDTimeStampedModel):
    class Kind(models.TextChoices):
        SIGNUP = "signup", "Signup bonus"
        DAILY_LOGIN = "daily_login", "Daily login"
        STREAK = "streak", "Login streak"
        FIRST_OFFER = "first_offer", "First offer"
        FIRST_WITHDRAWAL = "first_withdrawal", "First withdrawal"
        DEPOSIT = "deposit", "Deposit bonus"
        REFERRAL = "referral", "Referral bonus"
        CAMPAIGN = "campaign", "Campaign bonus"
        SEASONAL = "seasonal", "Seasonal bonus"

    class RewardMode(models.TextChoices):
        POINTS = "points", "Points"
        CASH = "cash", "Cash"
        BONUS = "bonus", "Bonus wallet"

    code = models.CharField(max_length=64, unique=True)
    name = models.CharField(max_length=120)
    kind = models.CharField(max_length=32, choices=Kind.choices, db_index=True)
    is_active = models.BooleanField(default=True, db_index=True)

    reward_mode = models.CharField(max_length=16, choices=RewardMode.choices, default=RewardMode.POINTS)
    points = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    cash = money_field()
    percentage = models.DecimalField(
        max_digits=6, decimal_places=3, null=True, blank=True,
        help_text="For deposit bonuses, e.g. 10.000 = 10% of the deposit.",
    )
    max_reward = money_field(null=True, blank=True)

    conditions = models.JSONField(
        default=dict, blank=True, help_text="e.g. {'min_deposit': '5.00'}"
    )
    streak_days = models.JSONField(
        default=list, blank=True, help_text="Per-day rewards, e.g. [10, 15, 20, 30, 50, 75, 100]"
    )
    starts_at = models.DateTimeField(null=True, blank=True)
    ends_at = models.DateTimeField(null=True, blank=True)
    max_claims_per_user = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.code})"


class Bonus(UUIDTimeStampedModel):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        ISSUED = "issued", "Issued"
        REJECTED = "rejected", "Rejected"
        REVERSED = "reversed", "Reversed"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="bonuses"
    )
    rule = models.ForeignKey(BonusRule, on_delete=models.PROTECT, related_name="bonuses")
    status = models.CharField(
        max_length=16, choices=Status.choices, default=Status.PENDING, db_index=True
    )
    reward = models.ForeignKey(
        "rewards.Reward", null=True, blank=True, on_delete=models.SET_NULL, related_name="bonuses"
    )
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["user", "rule", "status"])]

    def __str__(self):
        return f"bonus:{self.rule_id}:{self.user_id}"


class BonusClaim(UUIDTimeStampedModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="bonus_claims"
    )
    rule = models.ForeignKey(BonusRule, on_delete=models.PROTECT, related_name="claims")
    bonus = models.ForeignKey(
        Bonus, null=True, blank=True, on_delete=models.SET_NULL, related_name="claims"
    )
    claimed_at = models.DateTimeField(auto_now_add=True, db_index=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-claimed_at"]

    def __str__(self):
        return f"claim:{self.rule_id}:{self.user_id}"
