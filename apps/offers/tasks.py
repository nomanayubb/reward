"""Celery tasks for the offers module."""
import logging

from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task
def sync_offers():
    """Pull offers from every enabled CPA provider via its adapter."""
    from apps.cpa.models import CPAProvider
    from apps.cpa.providers.base import load_adapter

    from .models import CampaignQuota, Offer, OfferCategory

    created = updated = 0
    for provider in CPAProvider.objects.filter(is_enabled=True):
        try:
            adapter = load_adapter(provider)
            for item in adapter.get_offers():
                category = None
                if item.category:
                    category, _ = OfferCategory.objects.get_or_create(
                        slug=item.category.lower().replace(" ", "-"),
                        defaults={"name": item.category},
                    )
                offer, was_created = Offer.objects.update_or_create(
                    provider=provider,
                    external_id=item.external_id,
                    defaults={
                        "title": item.title,
                        "description": item.description,
                        "category": category,
                        "payout": item.payout,
                        "tracking_url": item.tracking_url,
                        "preview_image": item.preview_image,
                        "countries": item.countries,
                        "devices": item.devices,
                        "operating_systems": item.operating_systems,
                        "incentive_allowed": item.incentive_allowed,
                        "multiple_completion_allowed": item.multiple_completion_allowed,
                        "reinstall_allowed": item.reinstall_allowed,
                        "vpn_allowed": item.vpn_allowed,
                        "daily_user_limit": item.daily_user_limit,
                        "lifetime_user_limit": item.lifetime_user_limit,
                        "raw_payload": item.raw,
                    },
                )
                CampaignQuota.objects.get_or_create(offer=offer)
                created += int(was_created)
                updated += int(not was_created)

            provider.health = CPAProvider.Health.HEALTHY
            provider.last_sync_at = timezone.now()
            provider.last_error = ""
            provider.save(update_fields=["health", "last_sync_at", "last_error", "updated_at"])
        except Exception as exc:
            logger.exception("Offer sync failed for provider %s", provider.code)
            provider.health = CPAProvider.Health.DOWN
            provider.last_error = str(exc)[:255]
            provider.save(update_fields=["health", "last_error", "updated_at"])

    return {"created": created, "updated": updated}


@shared_task
def recalculate_campaign_quotas():
    """Reset rolling counters and un-pause offers whose caps have freed up."""
    from .models import CampaignQuota, Offer

    now = timezone.now()
    reset_counters = 0
    resumed = 0

    for quota in CampaignQuota.objects.select_related("offer"):
        changed = False
        if quota.last_hour_reset_at is None or (now - quota.last_hour_reset_at).total_seconds() >= 3600:
            quota.conversions_this_hour = 0
            quota.last_hour_reset_at = now
            changed = True
        if quota.last_day_reset_at is None or quota.last_day_reset_at.date() != now.date():
            quota.conversions_today = 0
            quota.last_day_reset_at = now
            changed = True
        if changed:
            quota.save()
            reset_counters += 1

        offer = quota.offer
        if offer.status == Offer.Status.PAUSED_BY_QUOTA:
            under_cap = (
                quota.daily_global_cap is None or quota.conversions_today < quota.daily_global_cap
            ) and (quota.hourly_cap is None or quota.conversions_this_hour < quota.hourly_cap)
            if under_cap:
                offer.status = Offer.Status.ACTIVE
                offer.save(update_fields=["status", "updated_at"])
                resumed += 1

    return {"reset": reset_counters, "resumed": resumed}
