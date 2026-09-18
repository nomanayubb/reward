"""Celery tasks for fraud analysis."""
import logging
from collections import Counter
from datetime import timedelta

from celery import shared_task
from django.contrib.auth import get_user_model
from django.db.models import Count
from django.utils import timezone

logger = logging.getLogger(__name__)

RAPID_CONVERSION_THRESHOLD = 10
RAPID_WINDOW_MINUTES = 60


@shared_task
def run_fraud_analysis():
    """Periodic sweep for multi-account / device reuse / rapid conversion signals."""
    from apps.offers.models import OfferConversion
    from apps.users.models import UserDevice

    from .models import FraudEvent
    from .services import record_fraud_event

    created = 0

    # Device reuse: same device hash on multiple accounts.
    device_counts = (
        UserDevice.objects.values("device_id_hash")
        .annotate(users=Count("user", distinct=True))
        .filter(users__gt=1)
    )
    for row in device_counts[:100]:
        device_hash = row["device_id_hash"]
        user_ids = set(
            UserDevice.objects.filter(device_id_hash=device_hash).values_list("user_id", flat=True)
        )
        for user_id in user_ids:
            if FraudEvent.objects.filter(
                user_id=user_id, kind=FraudEvent.Kind.DEVICE_REUSE, status=FraudEvent.Status.OPEN
            ).exists():
                continue
            user = get_user_model().objects.filter(pk=user_id).first()
            if user is None:
                continue
            record_fraud_event(
                user=user,
                kind=FraudEvent.Kind.DEVICE_REUSE,
                severity=FraudEvent.Severity.MEDIUM,
                evidence={"device_hash": device_hash, "users": row["users"]},
                device_hash=device_hash,
            )
            created += 1

    # Rapid conversions per user.
    since = timezone.now() - timedelta(minutes=RAPID_WINDOW_MINUTES)
    recent = OfferConversion.objects.filter(created_at__gte=since, status="approved").values_list(
        "user_id", flat=True
    )
    counts = Counter(recent)
    for user_id, count in counts.items():
        if count < RAPID_CONVERSION_THRESHOLD:
            continue
        if FraudEvent.objects.filter(
            user_id=user_id, kind=FraudEvent.Kind.RAPID_CONVERSION, status=FraudEvent.Status.OPEN
        ).exists():
            continue
        user = get_user_model().objects.filter(pk=user_id).first()
        if user is None:
            continue
        record_fraud_event(
            user=user,
            kind=FraudEvent.Kind.RAPID_CONVERSION,
            severity=FraudEvent.Severity.MEDIUM,
            evidence={"count": count, "window_minutes": RAPID_WINDOW_MINUTES},
        )
        created += 1

    return {"fraud_events_created": created}
