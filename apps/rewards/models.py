"""Reward engine: configurable rules + reward records.

Never hard-code "advertiser pays $2 -> user gets $1". A ``RewardRule`` decides
the user's share from the validated revenue event; ``Reward`` records the
result and links to the ledger transaction that moved the money.
"""
from django.conf import settings
from django.db import models

from apps.common.fields import money_field
from apps.common.models import UUIDTimeStampedModel


class RewardRule(UUIDTimeStampedModel):
    class Mode(models.TextChoices):
        CASH = "cash", "Cash"
        POINTS = "points", "Points"
        HYBRID = "hybrid", "Hybrid (cash + points)"

    class Source(models.TextChoices):
        GAME = "game", "Game"
        SURVEY = "survey", "Survey"
        OFFER = "offer", "Offer"
        BONUS = "bonus", "Bonus"
        REFERRAL = "referral", "Referral"
        ANY = "any", "Any source"

    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True, db_index=True)
    priority = models.PositiveIntegerField(
        default=100, help_text="Lower number = evaluated first."
    )

    source = models.CharField(max_length=16, choices=Source.choices, default=Source.ANY)

    # Optional scoping
    provider_code = models.CharField(max_length=64, blank=True)
    campaign_type = models.CharField(max_length=64, blank=True)
    country = models.CharField(max_length=2, blank=True)
    user_tier = models.CharField(max_length=16, blank=True)

    # Conditions evaluated against the conversion context (JSON DSL).
    conditions = models.JSONField(
        default=dict,
        blank=True,
        help_text='e.g. {"min_payout": "5.00", "max_payout": null}',
    )

    # Reward definition
    mode = models.CharField(max_length=16, choices=Mode.choices, default=Mode.CASH)
    reward_currency = models.CharField(
        max_length=8,
        default="PKR",
        help_text="Currency the user is paid in (ADR-015: PKR by default).",
    )
    user_percentage = models.DecimalField(
        max_digits=6, decimal_places=3, null=True, blank=True,
        help_text="Percent of validated revenue paid to the user, e.g. 40.000",
    )
    fixed_cash = money_field(null=True, blank=True)
    fixed_points = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    points_percentage = models.DecimalField(
        max_digits=6, decimal_places=3, null=True, blank=True,
        help_text="Percent of validated revenue converted to points.",
    )
    multiplier = models.DecimalField(max_digits=8, decimal_places=3, default=1)

    # Guard rails (see docs/DRD.md §156)
    max_user_reward = money_field(null=True, blank=True)
    requires_manual_approval = models.BooleanField(default=False)

    class Meta:
        ordering = ["priority", "name"]

    def __str__(self):
        return self.name


class Reward(UUIDTimeStampedModel):
    class Source(models.TextChoices):
        GAME = "game", "Game"
        SURVEY = "survey", "Survey"
        OFFER = "offer", "Offer"
        BONUS = "bonus", "Bonus"
        REFERRAL = "referral", "Referral"
        ADJUSTMENT = "adjustment", "Admin adjustment"
        PROMOTION = "promotion", "Promotion"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"
        REVERSED = "reversed", "Reversed"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="rewards"
    )
    source = models.CharField(max_length=16, choices=Source.choices, db_index=True)
    source_reference = models.CharField(
        max_length=191, blank=True, db_index=True,
        help_text="e.g. offer conversion id, game session id.",
    )
    rule = models.ForeignKey(
        RewardRule, null=True, blank=True, on_delete=models.SET_NULL, related_name="rewards"
    )

    gross_revenue = money_field(null=True, blank=True)
    platform_share = money_field(null=True, blank=True)
    user_reward = money_field()
    currency = models.CharField(max_length=8, default="PKR")
    points_reward = models.DecimalField(max_digits=20, decimal_places=2, default=0)

    status = models.CharField(
        max_length=16, choices=Status.choices, default=Status.PENDING, db_index=True
    )
    ledger_transaction = models.ForeignKey(
        "ledger.LedgerTransaction",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="rewards",
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="rewards_approved",
    )
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "status", "created_at"]),
            models.Index(fields=["source", "source_reference"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["source", "source_reference", "user"],
                condition=models.Q(source_reference__gt=""),
                name="uniq_reward_source_ref",
            )
        ]

    def __str__(self):
        return f"reward:{self.user_id}:{self.user_reward} {self.currency}"
