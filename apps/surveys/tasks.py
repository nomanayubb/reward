"""Celery tasks for the surveys module."""
import logging

from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task
def sync_surveys():
    """Pull surveys from every enabled survey provider."""
    from .models import Survey, SurveyProvider
    from .providers.base import load_adapter

    created = updated = 0
    for provider in SurveyProvider.objects.filter(is_enabled=True):
        try:
            adapter = load_adapter(provider)
            for item in adapter.get_surveys():
                _, was_created = Survey.objects.update_or_create(
                    provider=provider,
                    external_id=item.external_id,
                    defaults={
                        "title": item.title,
                        "description": item.description,
                        "category": item.category,
                        "country": item.country,
                        "language": item.language,
                        "device": item.device,
                        "estimated_minutes": item.estimated_minutes,
                        "payout": item.payout,
                        "qualification_rate": item.qualification_rate,
                        "daily_cap": item.daily_cap,
                        "user_cap": item.user_cap,
                        "raw_payload": item.raw,
                    },
                )
                created += int(was_created)
                updated += int(not was_created)

            provider.health = SurveyProvider.Health.HEALTHY
            provider.last_sync_at = timezone.now()
            provider.last_error = ""
            provider.save(update_fields=["health", "last_sync_at", "last_error", "updated_at"])
        except Exception as exc:
            logger.exception("Survey sync failed for provider %s", provider.code)
            provider.health = SurveyProvider.Health.DOWN
            provider.last_error = str(exc)[:255]
            provider.save(update_fields=["health", "last_error", "updated_at"])

    return {"created": created, "updated": updated}
