"""Provider reconciliation: compare provider reports against our records.

Networks report conversions and payouts; we record our own. This service
surfaces the difference (missing/extra conversions, payout gaps) so an admin
can raise a dispute with the network instead of silently absorbing it
(docs/DRD.md §124).
"""
from dataclasses import dataclass, field
from datetime import timedelta
from decimal import Decimal

from django.utils import timezone

from .models import OfferConversion


@dataclass
class ReconciliationResult:
    provider: str
    period_start: str
    period_end: str
    reported_conversions: int = 0
    reported_payout: Decimal = Decimal("0")
    local_conversions: int = 0
    local_payout: Decimal = Decimal("0")
    payout_difference: Decimal = Decimal("0")
    conversion_difference: int = 0
    report_rows: list = field(default_factory=list)

    @property
    def is_balanced(self) -> bool:
        return self.payout_difference == 0 and self.conversion_difference == 0


def reconcile_provider(provider, *, days: int = 7) -> ReconciliationResult:
    """Pull the provider report for the last ``days`` and compare it to ours."""
    from apps.cpa.providers.base import load_adapter

    now = timezone.now()
    since = now - timedelta(days=days)

    adapter = load_adapter(provider)
    report_rows = adapter.get_reporting_data(since=since, until=now)

    reported_conversions = sum(int(row.get("conversions", 0) or 0) for row in report_rows)
    reported_payout = sum(
        (Decimal(str(row.get("payout", 0) or 0)) for row in report_rows), Decimal("0")
    )

    local = OfferConversion.objects.filter(provider=provider, created_at__gte=since).exclude(
        status=OfferConversion.Status.REJECTED
    )
    local_conversions = local.count()
    local_payout = sum((conversion.payout for conversion in local), Decimal("0"))

    return ReconciliationResult(
        provider=provider.code,
        period_start=since.isoformat(),
        period_end=now.isoformat(),
        reported_conversions=reported_conversions,
        reported_payout=reported_payout,
        local_conversions=local_conversions,
        local_payout=local_payout,
        payout_difference=reported_payout - local_payout,
        conversion_difference=reported_conversions - local_conversions,
        report_rows=report_rows,
    )
