"""Celery tasks for analytics aggregation."""
import logging
from datetime import timedelta
from decimal import Decimal

from celery import shared_task
from django.db.models import Sum
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task
def generate_daily_statistics(day: str | None = None):
    """Aggregate core KPIs into DailyStatistic rows for the given day."""
    from apps.deposits.models import Deposit
    from apps.offers.models import OfferConversion
    from apps.rewards.models import Reward
    from apps.surveys.models import SurveyCompletion
    from apps.withdrawals.models import Withdrawal

    from .models import DailyStatistic

    if day:
        target = timezone.datetime.fromisoformat(day).date()
    else:
        target = timezone.localdate() - timedelta(days=1)

    def upsert(key: str, value, dimension: dict | None = None):
        DailyStatistic.objects.update_or_create(
            date=target, key=key, defaults={"value": value, "dimension": dimension or {}}
        )

    conversions = OfferConversion.objects.filter(created_at__date=target)
    rewards = Reward.objects.filter(created_at__date=target)
    surveys = SurveyCompletion.objects.filter(created_at__date=target)

    upsert("offers.conversions", conversions.count())
    upsert(
        "offers.revenue",
        conversions.aggregate(total=Sum("payout"))["total"] or Decimal("0"),
    )
    upsert(
        "rewards.user_cost",
        rewards.exclude(status=Reward.Status.REJECTED).aggregate(total=Sum("user_reward"))["total"]
        or Decimal("0"),
    )
    upsert("surveys.completions", surveys.count())
    upsert(
        "surveys.revenue",
        surveys.aggregate(total=Sum("payout"))["total"] or Decimal("0"),
    )
    upsert(
        "withdrawals.paid",
        Withdrawal.objects.filter(status=Withdrawal.Status.PAID, paid_at__date=target)
        .aggregate(total=Sum("amount"))["total"]
        or Decimal("0"),
    )
    upsert(
        "deposits.confirmed",
        Deposit.objects.filter(status=Deposit.Status.CONFIRMED, confirmed_at__date=target)
        .aggregate(total=Sum("amount"))["total"]
        or Decimal("0"),
    )

    return {"date": str(target), "keys": 6}
