"""Offer Eligibility Engine (docs/DRD.md §17-22).

Inputs: country, device, OS, age, account age, prior completions, IP risk,
VPN status, campaign rules, provider rules, daily/lifetime limits.
Output: ELIGIBLE / NOT_ELIGIBLE / REQUIRES_REVIEW with reasons.
"""
from dataclasses import dataclass, field
from enum import StrEnum

from django.utils import timezone


class Eligibility(StrEnum):
    ELIGIBLE = "eligible"
    NOT_ELIGIBLE = "not_eligible"
    REQUIRES_REVIEW = "requires_review"


@dataclass
class EligibilityResult:
    status: Eligibility
    reasons: list = field(default_factory=list)

    @property
    def is_eligible(self) -> bool:
        return self.status == Eligibility.ELIGIBLE

    def __bool__(self):
        return self.is_eligible


def _in_list(value, allowed: list) -> bool:
    return not allowed or value in allowed


def evaluate_offer(user, offer, *, context: dict | None = None) -> EligibilityResult:
    context = context or {}
    reasons: list[str] = []

    from apps.offers.models import Offer, OfferConversion
    from apps.users.models import UserRestriction

    if UserRestriction.objects.filter(
        user=user, type=UserRestriction.Type.OFFERS_DISABLED, is_active=True
    ).exists():
        return EligibilityResult(Eligibility.NOT_ELIGIBLE, ["offers_disabled_for_user"])

    if offer.status != Offer.Status.ACTIVE:
        reasons.append(f"offer_{offer.status}")

    if offer.expires_at and offer.expires_at <= timezone.now():
        reasons.append("offer_expired")

    # Compliance: incentivized traffic must be explicitly allowed.
    if not offer.incentive_allowed:
        reasons.append("incentive_not_allowed")

    country = context.get("country") or getattr(user, "country", "") or ""
    if offer.countries and country and country not in offer.countries:
        reasons.append("country_not_allowed")

    device = context.get("device", "")
    if offer.devices and device and not _in_list(device, offer.devices):
        reasons.append("device_not_allowed")

    os_name = context.get("os", "")
    if offer.operating_systems and os_name and not _in_list(os_name, offer.operating_systems):
        reasons.append("os_not_allowed")

    # Provider campaign quota
    quota = getattr(offer, "quota", None)
    if quota is not None:
        if quota.daily_global_cap is not None and quota.conversions_today >= quota.daily_global_cap:
            reasons.append("campaign_daily_cap_reached")
        if quota.hourly_cap is not None and quota.conversions_this_hour >= quota.hourly_cap:
            reasons.append("campaign_hourly_cap_reached")
        if quota.country_cap and country and quota.conversions_today >= quota.country_cap.get(country, 10**9):
            reasons.append("campaign_country_cap_reached")

    completed = (
        OfferConversion.objects.filter(user=user, offer=offer)
        .exclude(status=OfferConversion.Status.REJECTED)
        .count()
    )
    if completed and not offer.multiple_completion_allowed:
        reasons.append("already_completed")
    if completed >= offer.lifetime_user_limit:
        reasons.append("lifetime_user_limit_reached")

    today_count = (
        OfferConversion.objects.filter(
            user=user, offer=offer, created_at__date=timezone.localdate()
        )
        .exclude(status=OfferConversion.Status.REJECTED)
        .count()
    )
    if today_count >= offer.daily_user_limit:
        reasons.append("daily_user_limit_reached")

    if reasons:
        return EligibilityResult(Eligibility.NOT_ELIGIBLE, reasons)

    risk_score = getattr(getattr(user, "risk_profile", None), "risk_score", 0) or 0
    if risk_score >= 76:
        return EligibilityResult(Eligibility.REQUIRES_REVIEW, ["critical_risk_score"])
    if risk_score >= 51:
        return EligibilityResult(Eligibility.REQUIRES_REVIEW, ["high_risk_score"])

    return EligibilityResult(Eligibility.ELIGIBLE, [])
