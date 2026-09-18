"""Referrals: links, conversions and referral fraud signals.

Avoid unlimited MLM-style structures; referral depth/earnings are configurable
and capped by admin settings.
"""
from django.conf import settings
from django.db import models

from apps.common.fields import money_field
from apps.common.models import UUIDTimeStampedModel


class Referral(UUIDTimeStampedModel):
    class Status(models.TextChoices):
        REGISTERED = "registered", "Registered"
        QUALIFIED = "qualified", "Qualified"
        REJECTED = "rejected", "Rejected"

    referrer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="referrals_made"
    )
    referred = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="referral_source"
    )
    code_used = models.CharField(max_length=16, db_index=True)
    status = models.CharField(
        max_length=16, choices=Status.choices, default=Status.REGISTERED, db_index=True
    )

    signup_ip = models.GenericIPAddressField(null=True, blank=True)
    signup_device_hash = models.CharField(max_length=128, blank=True)
    fraud_flags = models.JSONField(default=dict, blank=True)
    qualified_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["referrer", "status"])]

    def __str__(self):
        return f"referral:{self.referrer_id}->{self.referred_id}"


class ReferralConversion(UUIDTimeStampedModel):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"
        REVERSED = "reversed", "Reversed"

    referral = models.ForeignKey(
        Referral, on_delete=models.CASCADE, related_name="conversions"
    )
    source = models.CharField(max_length=32, help_text="offer / survey / game / deposit")
    source_reference = models.CharField(max_length=191, blank=True)
    gross_amount = money_field()
    reward_amount = money_field()
    reward = models.ForeignKey(
        "rewards.Reward", null=True, blank=True, on_delete=models.SET_NULL, related_name="referral_conversions"
    )
    status = models.CharField(
        max_length=16, choices=Status.choices, default=Status.PENDING, db_index=True
    )

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["referral", "status"])]

    def __str__(self):
        return f"ref-conv:{self.referral_id}:{self.status}"
