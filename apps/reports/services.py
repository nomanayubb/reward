"""Report generation services (CSV exports).

Reports are generated from the transactional tables; as volume grows they can
be moved to the analytics pipeline without changing the admin workflow.
"""
import csv
import io
from datetime import timedelta

from django.core.files.base import ContentFile
from django.utils import timezone

from .models import ReportJob


def _users_rows():
    from django.contrib.auth import get_user_model

    for user in get_user_model().objects.order_by("date_joined").iterator():
        yield [
            str(user.id),
            user.email,
            user.status,
            user.country,
            user.date_joined.isoformat(),
        ]


def _withdrawals_rows():
    from apps.withdrawals.models import Withdrawal

    queryset = Withdrawal.objects.select_related("user", "method").order_by("requested_at")
    for withdrawal in queryset.iterator():
        yield [
            str(withdrawal.id),
            withdrawal.user.email,
            str(withdrawal.amount),
            withdrawal.currency,
            withdrawal.status,
            withdrawal.method.type,
            withdrawal.requested_at.isoformat(),
            withdrawal.paid_at.isoformat() if withdrawal.paid_at else "",
            withdrawal.payment_reference,
        ]


def _rewards_rows():
    from apps.rewards.models import Reward

    queryset = Reward.objects.select_related("user").order_by("created_at")
    for reward in queryset.iterator():
        yield [
            str(reward.id),
            reward.user.email,
            reward.source,
            str(reward.user_reward),
            reward.currency,
            str(reward.points_reward),
            reward.status,
            reward.created_at.isoformat(),
        ]


def _offer_conversions_rows():
    from apps.offers.models import OfferConversion

    queryset = OfferConversion.objects.select_related("user", "offer", "provider").order_by(
        "created_at"
    )
    for conversion in queryset.iterator():
        yield [
            str(conversion.id),
            conversion.user.email,
            conversion.offer.title,
            conversion.provider.code,
            str(conversion.payout),
            str(conversion.user_reward),
            conversion.status,
            conversion.created_at.isoformat(),
        ]


HEADERS = {
    ReportJob.Kind.USERS: ["id", "email", "status", "country", "date_joined"],
    ReportJob.Kind.WITHDRAWALS: [
        "id",
        "user",
        "amount",
        "currency",
        "status",
        "method",
        "requested_at",
        "paid_at",
        "reference",
    ],
    ReportJob.Kind.FINANCIAL: [
        "id",
        "user",
        "source",
        "user_reward",
        "currency",
        "points_reward",
        "status",
        "created_at",
    ],
    ReportJob.Kind.OFFERS: [
        "id",
        "user",
        "offer",
        "provider",
        "payout",
        "user_reward",
        "status",
        "created_at",
    ],
}

ROW_BUILDERS = {
    ReportJob.Kind.USERS: _users_rows,
    ReportJob.Kind.WITHDRAWALS: _withdrawals_rows,
    ReportJob.Kind.FINANCIAL: _rewards_rows,
    ReportJob.Kind.OFFERS: _offer_conversions_rows,
}


def generate_report(job: ReportJob) -> ReportJob:
    """Build the CSV for a job and attach it to ``job.file``."""
    if job.kind not in ROW_BUILDERS:
        job.status = ReportJob.Status.FAILED
        job.error = f"Unsupported report kind: {job.kind}"
        job.save(update_fields=["status", "error", "updated_at"])
        return job

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(HEADERS[job.kind])
    for row in ROW_BUILDERS[job.kind]():
        writer.writerow(row)

    filename = f"{job.kind}-{timezone.now().strftime('%Y%m%d-%H%M%S')}.csv"
    job.file.save(filename, ContentFile(buffer.getvalue().encode("utf-8")), save=False)
    job.status = ReportJob.Status.READY
    job.error = ""
    job.expires_at = timezone.now() + timedelta(hours=24)
    job.save(update_fields=["file", "status", "error", "expires_at", "updated_at"])
    return job
