"""Ad serving: weighted rotation + frequency capping (ADR-013).

House ads and direct sponsorships come first; nothing here rewards users for
clicking ads. A campaign is only served when its provider is enabled, it is
inside its schedule and the user has not exceeded the frequency caps.
"""
import random
from collections import namedtuple
from datetime import timedelta

from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from .models import AdCampaign, AdClick, AdImpression, AdPlacement

AdSlot = namedtuple("AdSlot", ["campaign", "impression"])


def _frequency_ok(campaign: AdCampaign, user, now) -> bool:
    if user is None or not getattr(user, "is_authenticated", False):
        return True

    hourly = AdImpression.objects.filter(
        campaign=campaign, user=user, created_at__gte=now - timedelta(hours=1)
    ).count()
    if hourly >= campaign.max_per_hour:
        return False

    daily = AdImpression.objects.filter(
        campaign=campaign, user=user, created_at__date=now.date()
    ).count()
    if daily >= campaign.max_per_day:
        return False

    last = (
        AdImpression.objects.filter(campaign=campaign, user=user)
        .order_by("-created_at")
        .first()
    )
    if last is None:
        return True
    return last.created_at <= now - timedelta(minutes=campaign.min_interval_minutes)


def select_campaign(placement_code: str, user=None):
    """Return ``(campaign, placement)`` or ``(None, placement|None)``."""
    now = timezone.now()
    placement = AdPlacement.objects.filter(code=placement_code, is_active=True).first()
    if placement is None:
        return None, None

    candidates = (
        AdCampaign.objects.filter(
            placements=placement,
            status=AdCampaign.Status.ACTIVE,
            provider__is_enabled=True,
        )
        .filter(Q(starts_at__isnull=True) | Q(starts_at__lte=now))
        .filter(Q(ends_at__isnull=True) | Q(ends_at__gte=now))
        .select_related("provider")
    )

    eligible = [campaign for campaign in candidates if _frequency_ok(campaign, user, now)]
    if not eligible:
        return None, placement

    weights = [max(1, campaign.weight) for campaign in eligible]
    return random.choices(eligible, weights=weights, k=1)[0], placement


@transaction.atomic
def record_impression(*, campaign: AdCampaign, placement=None, user=None, ip=None, device_hash="") -> AdImpression:
    return AdImpression.objects.create(
        campaign=campaign,
        placement=placement,
        user=user if getattr(user, "is_authenticated", False) else None,
        ip_address=ip,
        device_id_hash=device_hash[:128],
    )


@transaction.atomic
def record_click(*, impression: AdImpression, user=None, ip=None) -> AdClick:
    return AdClick.objects.create(
        campaign=impression.campaign,
        impression=impression,
        user=user if getattr(user, "is_authenticated", False) else None,
        ip_address=ip,
    )


def serve_ad(placement_code: str, request) -> AdSlot | None:
    """Select a campaign for a request, record the impression and return it."""
    campaign, placement = select_campaign(placement_code, user=request.user)
    if campaign is None:
        return None

    impression = record_impression(
        campaign=campaign,
        placement=placement,
        user=request.user,
        ip=request.META.get("REMOTE_ADDR"),
    )
    return AdSlot(campaign=campaign, impression=impression)
