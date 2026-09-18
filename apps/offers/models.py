"""CPA / offerwall: offers, quotas, clicks, conversions and raw postbacks.

Compliance is data, not code: each offer stores whether incentivized traffic,
VPN, emulators, reinstalls and multiple completions are allowed. The
eligibility engine (apps/offers/eligibility.py) enforces these rules.
"""
from django.conf import settings
from django.db import models

from apps.common.fields import money_field
from apps.common.models import UUIDTimeStampedModel


class OfferCategory(UUIDTimeStampedModel):
    name = models.CharField(max_length=80)
    slug = models.SlugField(max_length=80, unique=True)
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["sort_order", "name"]
        verbose_name_plural = "offer categories"

    def __str__(self):
        return self.name


class Offer(UUIDTimeStampedModel):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        PAUSED = "paused", "Paused"
        EXPIRED = "expired", "Expired"
        PAUSED_BY_QUOTA = "paused_by_quota", "Paused by quota"
        DISABLED_BY_COMPLIANCE = "disabled_by_compliance", "Disabled by compliance"

    class RewardMode(models.TextChoices):
        CASH = "cash", "Cash"
        POINTS = "points", "Points"
        HYBRID = "hybrid", "Hybrid"

    provider = models.ForeignKey(
        "cpa.CPAProvider", on_delete=models.CASCADE, related_name="offers"
    )
    external_id = models.CharField(max_length=191, db_index=True)
    category = models.ForeignKey(
        OfferCategory, null=True, blank=True, on_delete=models.SET_NULL, related_name="offers"
    )

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    advertiser = models.CharField(max_length=120, blank=True)

    payout = money_field(help_text="Advertiser / provider payout.")
    user_reward = money_field(help_text="Configured user reward.")
    currency = models.CharField(max_length=8, default="USD")
    reward_mode = models.CharField(
        max_length=16, choices=RewardMode.choices, default=RewardMode.CASH
    )
    points_reward = models.DecimalField(max_digits=20, decimal_places=2, default=0)

    tracking_url = models.URLField(max_length=1000, blank=True)
    preview_image = models.URLField(max_length=1000, blank=True)

    countries = models.JSONField(default=list, blank=True, help_text="Empty = all countries")
    devices = models.JSONField(default=list, blank=True)
    operating_systems = models.JSONField(default=list, blank=True)
    min_age = models.PositiveSmallIntegerField(default=0)

    # Compliance flags (docs/DRD.md §17)
    incentive_allowed = models.BooleanField(default=False, db_index=True)
    traffic_source_allowed = models.JSONField(default=list, blank=True)
    vpn_allowed = models.BooleanField(default=False)
    proxy_allowed = models.BooleanField(default=False)
    emulator_allowed = models.BooleanField(default=False)
    multiple_completion_allowed = models.BooleanField(default=False)
    reinstall_allowed = models.BooleanField(default=False)
    daily_user_limit = models.PositiveIntegerField(default=1)
    lifetime_user_limit = models.PositiveIntegerField(default=1)

    status = models.CharField(
        max_length=32, choices=Status.choices, default=Status.ACTIVE, db_index=True
    )
    is_featured = models.BooleanField(default=False)
    rank_score = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    expires_at = models.DateTimeField(null=True, blank=True)

    raw_payload = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-rank_score", "-payout"]
        constraints = [
            models.UniqueConstraint(
                fields=["provider", "external_id"], name="uniq_offer_provider_external"
            )
        ]
        indexes = [
            models.Index(fields=["status", "incentive_allowed"]),
            models.Index(fields=["reward_mode"]),
        ]

    def __str__(self):
        return f"offer:{self.title[:50]}"


class CampaignQuota(UUIDTimeStampedModel):
    """Provider campaign caps. Enforced before showing/completing offers."""

    offer = models.OneToOneField(Offer, on_delete=models.CASCADE, related_name="quota")

    daily_global_cap = models.PositiveIntegerField(null=True, blank=True)
    hourly_cap = models.PositiveIntegerField(null=True, blank=True)
    daily_user_cap = models.PositiveIntegerField(null=True, blank=True)
    lifetime_user_cap = models.PositiveIntegerField(null=True, blank=True)
    country_cap = models.JSONField(default=dict, blank=True, help_text='{"PK": 100}')

    conversions_today = models.PositiveIntegerField(default=0)
    conversions_this_hour = models.PositiveIntegerField(default=0)
    conversions_lifetime = models.PositiveIntegerField(default=0)

    last_hour_reset_at = models.DateTimeField(null=True, blank=True)
    last_day_reset_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"quota:{self.offer_id}"


class OfferClick(UUIDTimeStampedModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="offer_clicks"
    )
    offer = models.ForeignKey(Offer, on_delete=models.CASCADE, related_name="clicks")
    click_id = models.CharField(max_length=64, unique=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    device_id_hash = models.CharField(max_length=128, blank=True)
    user_agent = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["user", "offer", "created_at"])]

    def __str__(self):
        return f"click:{self.click_id}"


class OfferConversion(UUIDTimeStampedModel):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"
        REVERSED = "reversed", "Reversed"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="offer_conversions"
    )
    offer = models.ForeignKey(Offer, on_delete=models.PROTECT, related_name="conversions")
    provider = models.ForeignKey(
        "cpa.CPAProvider", on_delete=models.PROTECT, related_name="conversions"
    )
    click = models.ForeignKey(
        OfferClick, null=True, blank=True, on_delete=models.SET_NULL, related_name="conversions"
    )

    external_conversion_id = models.CharField(max_length=191, db_index=True)
    payout = money_field()
    user_reward = money_field()
    status = models.CharField(
        max_length=16, choices=Status.choices, default=Status.PENDING, db_index=True
    )

    reward = models.ForeignKey(
        "rewards.Reward", null=True, blank=True, on_delete=models.SET_NULL, related_name="offer_conversions"
    )
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    device_id_hash = models.CharField(max_length=128, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["provider", "external_conversion_id"],
                name="uniq_conversion_provider_external",
            )
        ]
        indexes = [
            models.Index(fields=["status", "created_at"]),
            models.Index(fields=["user", "offer"]),
        ]

    def __str__(self):
        return f"conversion:{self.external_conversion_id}:{self.status}"


class OfferPostback(UUIDTimeStampedModel):
    provider = models.ForeignKey(
        "cpa.CPAProvider", on_delete=models.CASCADE, related_name="postbacks"
    )
    conversion = models.ForeignKey(
        OfferConversion, null=True, blank=True, on_delete=models.SET_NULL, related_name="postbacks"
    )
    received_at = models.DateTimeField(auto_now_add=True, db_index=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    headers = models.JSONField(default=dict, blank=True)
    payload = models.JSONField(default=dict, blank=True)
    signature_valid = models.BooleanField(default=False)
    processing_result = models.CharField(max_length=64, blank=True)
    processing_note = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["-received_at"]

    def __str__(self):
        return f"postback:{self.provider_id}:{self.processing_result}"
