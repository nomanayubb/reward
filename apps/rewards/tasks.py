"""Celery tasks for the rewards module."""
import logging
from datetime import timedelta

from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)

AUTO_APPROVE_AFTER_MINUTES = 30


@shared_task
def process_pending_rewards():
    """Auto-approve pending rewards that do not require manual approval."""
    from .models import Reward
    from .services import RewardService

    cutoff = timezone.now() - timedelta(minutes=AUTO_APPROVE_AFTER_MINUTES)
    approved = 0

    pending = Reward.objects.filter(status=Reward.Status.PENDING, created_at__lte=cutoff).select_related(
        "rule"
    )
    for reward in pending:
        rule = reward.rule
        if rule is not None and rule.requires_manual_approval:
            continue
        if (reward.metadata or {}).get("held"):
            continue
        RewardService.approve(reward)
        approved += 1

    return {"approved": approved}
