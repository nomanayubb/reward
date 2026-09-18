"""CPA offer services: clicks, postback ingestion, quotas.

Postback processing is idempotent (unique provider + external conversion id),
signature-validated and stores the raw payload for disputes (docs/DRD.md §23-24,
§105, §142).
"""
import logging

from django.db import transaction
from django.utils import timezone

from apps.rewards.models import Reward
from apps.rewards.services import RewardService

from .eligibility import evaluate_offer
from .models import CampaignQuota, Offer, OfferClick, OfferConversion, OfferPostback

logger = logging.getLogger(__name__)


def record_click(user, offer: Offer, *, click_id: str, ip=None, device_hash="", user_agent="") -> OfferClick:
    return OfferClick.objects.create(
        user=user,
        offer=offer,
        click_id=click_id,
        ip_address=ip,
        device_id_hash=device_hash,
        user_agent=user_agent[:255],
    )


def get_click_url(user, offer: Offer, click: OfferClick) -> str:
    """Provider tracking URL for the click, via the provider adapter."""
    from apps.cpa.providers.base import load_adapter

    adapter = load_adapter(offer.provider)
    url = adapter.track_click(offer, user, click.click_id)
    return url or offer.tracking_url


@transaction.atomic
def bump_quota(offer: Offer, *, country: str = "") -> CampaignQuota:
    quota, _ = CampaignQuota.objects.select_for_update().get_or_create(offer=offer)
    now = timezone.now()

    if quota.last_hour_reset_at is None or (now - quota.last_hour_reset_at).total_seconds() >= 3600:
        quota.conversions_this_hour = 0
        quota.last_hour_reset_at = now
    if quota.last_day_reset_at is None or quota.last_day_reset_at.date() != now.date():
        quota.conversions_today = 0
        quota.last_day_reset_at = now

    quota.conversions_today += 1
    quota.conversions_this_hour += 1
    quota.conversions_lifetime += 1

    if quota.daily_global_cap is not None and quota.conversions_today >= quota.daily_global_cap:
        offer.status = Offer.Status.PAUSED_BY_QUOTA
        offer.save(update_fields=["status", "updated_at"])

    quota.save()
    return quota


@transaction.atomic
def process_postback(provider, payload: dict, headers: dict | None = None, ip=None):
    """Ingest a provider postback. Returns ``(conversion, created)``.

    A replayed postback returns the original conversion with ``created=False``
    and never pays twice.
    """
    from apps.cpa.providers.base import load_adapter

    adapter = load_adapter(provider)
    postback = OfferPostback.objects.create(
        provider=provider,
        payload=payload,
        headers=headers or {},
        ip_address=ip,
    )

    if not adapter.validate_signature(payload, headers):
        postback.processing_result = "invalid_signature"
        postback.save(update_fields=["processing_result", "updated_at"])
        logger.warning("Rejected postback with invalid signature from %s", provider.code)
        return None, False

    try:
        normalized = adapter.process_postback(payload, headers)
    except Exception as exc:  # malformed payload from provider
        postback.processing_result = "parse_error"
        postback.processing_note = str(exc)[:255]
        postback.save(update_fields=["processing_result", "processing_note", "updated_at"])
        logger.exception("Failed to parse postback from %s", provider.code)
        return None, False

    postback.processing_note = normalized.reason[:255]

    existing = OfferConversion.objects.filter(
        provider=provider, external_conversion_id=normalized.external_conversion_id
    ).first()
    if existing is not None:
        postback.conversion = existing
        postback.processing_result = "duplicate"
        postback.save(update_fields=["conversion", "processing_result", "processing_note", "updated_at"])
        return existing, False

    click = (
        OfferClick.objects.select_related("user", "offer")
        .filter(click_id=normalized.user_identifier)
        .first()
    )
    if click is None:
        postback.processing_result = "unknown_user"
        postback.save(update_fields=["processing_result", "processing_note", "updated_at"])
        return None, False

    user, offer = click.user, click.offer
    country = getattr(user, "country", "") or ""

    if normalized.status != "approved":
        conversion = OfferConversion.objects.create(
            user=user,
            offer=offer,
            provider=provider,
            click=click,
            external_conversion_id=normalized.external_conversion_id,
            payout=normalized.payout,
            user_reward=0,
            status=OfferConversion.Status.REJECTED,
            ip_address=ip,
            device_id_hash=click.device_id_hash,
        )
        postback.conversion = conversion
        postback.processing_result = "rejected_by_provider"
        postback.save(update_fields=["conversion", "processing_result", "processing_note", "updated_at"])
        return conversion, True

    eligibility = evaluate_offer(
        user,
        offer,
        context={"country": country, "device": click.device_id_hash and "mobile" or "", "os": ""},
    )
    if not eligibility.is_eligible:
        conversion = OfferConversion.objects.create(
            user=user,
            offer=offer,
            provider=provider,
            click=click,
            external_conversion_id=normalized.external_conversion_id,
            payout=normalized.payout,
            user_reward=0,
            status=OfferConversion.Status.REJECTED,
            ip_address=ip,
            device_id_hash=click.device_id_hash,
        )
        postback.conversion = conversion
        postback.processing_result = "not_eligible"
        postback.processing_note = ",".join(eligibility.reasons)[:255]
        postback.save(update_fields=["conversion", "processing_result", "processing_note", "updated_at"])
        return conversion, True

    conversion = OfferConversion.objects.create(
        user=user,
        offer=offer,
        provider=provider,
        click=click,
        external_conversion_id=normalized.external_conversion_id,
        payout=normalized.payout,
        user_reward=0,
        status=OfferConversion.Status.PENDING,
        ip_address=ip,
        device_id_hash=click.device_id_hash,
    )

    reward, _ = RewardService.award(
        user=user,
        source=Reward.Source.OFFER,
        source_reference=str(conversion.id),
        gross_revenue=normalized.payout,
        context={
            "provider_code": provider.code,
            "campaign_type": "offer",
            "country": country,
            "offer_id": str(offer.id),
        },
    )

    conversion.reward = reward
    conversion.user_reward = reward.user_reward
    conversion.status = OfferConversion.Status.APPROVED
    conversion.approved_at = timezone.now()
    conversion.save(update_fields=["reward", "user_reward", "status", "approved_at", "updated_at"])

    bump_quota(offer, country=country)

    postback.conversion = conversion
    postback.processing_result = "approved"
    postback.save(update_fields=["conversion", "processing_result", "processing_note", "updated_at"])

    from apps.automation.services import emit_event

    emit_event(
        "OFFER_CONVERTED",
        user,
        {"offer_id": str(offer.id), "conversion_id": str(conversion.id), "payout": str(normalized.payout)},
    )
    return conversion, True
