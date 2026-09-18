"""Advertising: providers, campaigns, placements, impressions and clicks.

Never reward users for clicking ads unless the ad program explicitly permits
incentivized traffic. Frequency capping and weighted rotation live here.
"""
from django.conf import settings
from django.db import models

from apps.common.fields import money_field
from apps.common.models import UUIDTimeStampedModel


class AdProvider(UUIDTimeStampedModel):
    class Kind(models.TextChoices):
        GOOGLE = "google", "Google AdSense/AdX"
        DIRECT = "direct", "Direct advertiser"
        NETWORK = "network", "Ad network"
        HOUSE = "house", "House ads"
        AFFILIATE = "affiliate", "Affiliate"

    code = models.CharField(max_length=64, unique=True)
    name = models.CharField(max_length=120)
    kind = models.CharField(max_length=16, choices=Kind.choices)
    is_enabled = models.BooleanField(default=False, db_index=True)
    config = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.code})"


class AdPlacement(UUIDTimeStampedModel):
    code = models.CharField(max_length=64, unique=True, help_text="e.g. homepage, game_page")
    name = models.CharField(max_length=120)
    description = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class AdCampaign(UUIDTimeStampedModel):
    class AdType(models.TextChoices):
        BANNER = "banner", "Banner"
        NATIVE = "native", "Native"
        INTERSTITIAL = "interstitial", "Interstitial"
        VIDEO = "video", "Video"
        REWARDED = "rewarded", "Rewarded"
        SPONSORSHIP = "sponsorship", "Direct sponsorship"

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        ACTIVE = "active", "Active"
        PAUSED = "paused", "Paused"
        EXPIRED = "expired", "Expired"

    provider = models.ForeignKey(AdProvider, on_delete=models.CASCADE, related_name="campaigns")
    name = models.CharField(max_length=120)
    ad_type = models.CharField(max_length=16, choices=AdType.choices)

    image = models.ImageField(upload_to="ads/", null=True, blank=True)
    html_snippet = models.TextField(blank=True)
    target_url = models.URLField(max_length=1000, blank=True)

    placements = models.ManyToManyField(AdPlacement, blank=True, related_name="campaigns")
    weight = models.PositiveIntegerField(default=100, help_text="Weighted rotation weight.")

    status = models.CharField(
        max_length=16, choices=Status.choices, default=Status.DRAFT, db_index=True
    )
    starts_at = models.DateTimeField(null=True, blank=True)
    ends_at = models.DateTimeField(null=True, blank=True)
    budget = money_field(null=True, blank=True)
    spent = money_field()

    # Frequency control defaults (admin configurable per campaign)
    max_per_hour = models.PositiveIntegerField(default=3)
    min_interval_minutes = models.PositiveIntegerField(default=10)
    max_per_day = models.PositiveIntegerField(default=10)

    class Meta:
        ordering = ["-weight", "name"]

    def __str__(self):
        return self.name


class AdImpression(UUIDTimeStampedModel):
    campaign = models.ForeignKey(AdCampaign, on_delete=models.CASCADE, related_name="impressions")
    placement = models.ForeignKey(
        AdPlacement, null=True, blank=True, on_delete=models.SET_NULL, related_name="impressions"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="ad_impressions",
    )
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    device_id_hash = models.CharField(max_length=128, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["campaign", "created_at"]),
            models.Index(fields=["user", "created_at"]),
        ]

    def __str__(self):
        return f"impression:{self.campaign_id}"


class AdClick(UUIDTimeStampedModel):
    impression = models.ForeignKey(
        AdImpression, null=True, blank=True, on_delete=models.SET_NULL, related_name="clicks"
    )
    campaign = models.ForeignKey(AdCampaign, on_delete=models.CASCADE, related_name="clicks")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="ad_clicks",
    )
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"ad-click:{self.campaign_id}"
