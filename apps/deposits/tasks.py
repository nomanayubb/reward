"""Celery tasks for the deposits module."""
import logging

from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task
def expire_deposits():
    """Mark unpaid deposits past their window as expired."""
    from .models import Deposit

    now = timezone.now()
    expired = Deposit.objects.filter(
        status__in=[Deposit.Status.CREATED, Deposit.Status.AWAITING_PAYMENT],
        expires_at__lte=now,
    ).update(status=Deposit.Status.EXPIRED, updated_at=now)
    return {"expired": expired}
