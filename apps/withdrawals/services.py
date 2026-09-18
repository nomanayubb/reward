"""Withdrawal services: request, review, approve, pay, reject/refund.

Money is reserved (CASH -> LOCKED) the moment a request is created, so two
simultaneous requests can never spend the same balance (docs/DRD.md §106-107,
§143).
"""
import logging
from datetime import timedelta
from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from apps.adminpanel.settings import get_setting
from apps.ledger import services as ledger
from apps.ledger.models import LedgerTransaction
from apps.payments.services import convert
from apps.wallets.models import WalletAccount
from apps.wallets.services import get_account, system_account

from .models import Withdrawal, WithdrawalMethod

logger = logging.getLogger(__name__)


class WithdrawalError(Exception):
    """Raised when a withdrawal cannot be requested or transitioned."""


def _limit_in_currency(key: str, currency: str, default: str) -> Decimal:
    """Limits are configured in PKR and converted for other wallet currencies."""
    pkr_value = Decimal(str(get_setting(key, default)))
    if currency == "PKR" or pkr_value == 0:
        return pkr_value
    converted, _ = convert(pkr_value, "PKR", currency)
    return converted


def _fee_for(amount: Decimal) -> Decimal:
    percent = Decimal(str(get_setting("WITHDRAWAL_FEE_PERCENT", 0)))
    fixed = Decimal(str(get_setting("WITHDRAWAL_FEE_FIXED", 0)))
    return (amount * percent / Decimal("100") + fixed).quantize(Decimal("0.00000001"))


def _validate_request(user, amount: Decimal, method: WithdrawalMethod, currency: str) -> None:
    from apps.kyc.models import KYCVerification
    from apps.users.models import UserRestriction

    if not get_setting("WITHDRAWALS_ENABLED", True):
        raise WithdrawalError("Withdrawals are temporarily disabled.")

    if UserRestriction.objects.filter(
        user=user, type=UserRestriction.Type.WITHDRAWAL_DISABLED, is_active=True
    ).exists():
        raise WithdrawalError("Withdrawals are disabled for this account.")

    minimum = _limit_in_currency("MIN_WITHDRAWAL_PKR", currency, "500.00")
    maximum = _limit_in_currency("MAX_WITHDRAWAL_PKR", currency, "100000.00")
    if amount < minimum:
        raise WithdrawalError(f"Minimum withdrawal is {minimum} {currency}.")
    if amount > maximum:
        raise WithdrawalError(f"Maximum withdrawal is {maximum} {currency}.")

    kyc_threshold = _limit_in_currency("KYC_THRESHOLD_PKR", currency, "5000.00")
    if kyc_threshold > 0 and amount >= kyc_threshold:
        kyc = KYCVerification.objects.filter(user=user, status=KYCVerification.Status.APPROVED).exists()
        if not kyc:
            raise WithdrawalError("KYC verification is required for this withdrawal amount.")

    cooldown_hours = int(get_setting("WITHDRAWAL_COOLDOWN_HOURS", 0))
    if cooldown_hours:
        cutoff = timezone.now() - timedelta(hours=cooldown_hours)
        recent = Withdrawal.objects.filter(user=user, requested_at__gte=cutoff).exclude(
            status=Withdrawal.Status.REJECTED
        )
        if recent.exists():
            raise WithdrawalError("Withdrawal cooldown is active; try again later.")

    if not method.is_verified and get_setting("REQUIRE_VERIFIED_WITHDRAWAL_METHOD", False):
        raise WithdrawalError("This withdrawal method is not verified yet.")


@transaction.atomic
def request_withdrawal(
    *, user, method: WithdrawalMethod, amount, currency: str | None = None
) -> Withdrawal:
    from apps.wallets.services import get_wallet

    amount = Decimal(str(amount)).quantize(Decimal("0.00000001"))
    if currency is None:
        currency = get_wallet(user).currency
    _validate_request(user, amount, method, currency)

    account = get_account(user, WalletAccount.Type.CASH, currency)
    locked_account = WalletAccount.objects.select_for_update().get(pk=account.pk)
    if locked_account.available < amount:
        raise WithdrawalError("Insufficient available balance.")

    fee = _fee_for(amount)
    payout_mode = get_setting("PAYOUT_MODE", "manual")
    auto_threshold = _limit_in_currency("AUTO_PAYOUT_MAX_PKR", currency, "1500.00")
    if payout_mode == "auto":
        resolved_mode = "auto"
    elif payout_mode == "hybrid":
        resolved_mode = "auto" if amount < auto_threshold else "manual"
    else:
        resolved_mode = "manual"

    risk_score = getattr(getattr(user, "risk_profile", None), "risk_score", 0) or 0
    risk_level = (
        Withdrawal.Risk.HIGH
        if risk_score >= 76
        else Withdrawal.Risk.MEDIUM
        if risk_score >= 51
        else Withdrawal.Risk.LOW
    )

    withdrawal = Withdrawal.objects.create(
        user=user,
        method=method,
        amount=amount,
        fee=fee,
        net_amount=amount - fee,
        currency=currency,
        status=Withdrawal.Status.REQUESTED,
        risk_level=risk_level,
        payout_mode=resolved_mode,
        requires_dual_approval=amount
        >= _limit_in_currency("DUAL_APPROVAL_THRESHOLD_PKR", currency, "25000.00"),
    )

    txn, _ = ledger.post_transaction(
        type=LedgerTransaction.Type.WITHDRAWAL_RESERVE,
        entries=[
            (locked_account, -amount),
            (get_account(user, WalletAccount.Type.LOCKED, currency), amount),
        ],
        reference=str(withdrawal.id),
        description="Withdrawal reserved",
        metadata={"withdrawal_id": str(withdrawal.id), "user_id": str(user.pk)},
        idempotency_key=f"withdrawal:{withdrawal.id}:reserve",
    )
    withdrawal.reserve_transaction = txn
    withdrawal.save(update_fields=["reserve_transaction", "updated_at"])

    from apps.automation.services import emit_event

    emit_event("WITHDRAWAL_REQUESTED", user, {"withdrawal_id": str(withdrawal.id), "amount": str(amount)})
    return withdrawal


@transaction.atomic
def approve_withdrawal(withdrawal: Withdrawal, *, approved_by=None, second_approver=None) -> Withdrawal:
    withdrawal = Withdrawal.objects.select_for_update().get(pk=withdrawal.pk)
    if withdrawal.status not in {Withdrawal.Status.REQUESTED, Withdrawal.Status.UNDER_REVIEW}:
        raise WithdrawalError(f"Cannot approve a withdrawal in status '{withdrawal.status}'.")

    if withdrawal.requires_dual_approval and approved_by is not None:
        if withdrawal.approved_by_id and withdrawal.approved_by_id != approved_by.pk:
            withdrawal.second_approver = second_approver or approved_by
        else:
            withdrawal.approved_by = approved_by
    elif approved_by is not None:
        withdrawal.approved_by = approved_by

    if withdrawal.requires_dual_approval and not (
        withdrawal.approved_by_id and withdrawal.second_approver_id
    ):
        withdrawal.status = Withdrawal.Status.UNDER_REVIEW
        withdrawal.reviewed_at = timezone.now()
        withdrawal.save()
        return withdrawal

    withdrawal.status = Withdrawal.Status.PROCESSING
    withdrawal.reviewed_at = timezone.now()
    withdrawal.save()
    return withdrawal


@transaction.atomic
def mark_paid(withdrawal: Withdrawal, *, reference: str = "", proof=None) -> Withdrawal:
    withdrawal = Withdrawal.objects.select_for_update().get(pk=withdrawal.pk)
    if withdrawal.status not in {Withdrawal.Status.APPROVED, Withdrawal.Status.PROCESSING}:
        raise WithdrawalError(f"Cannot pay a withdrawal in status '{withdrawal.status}'.")

    ledger.post_transaction(
        type=LedgerTransaction.Type.WITHDRAWAL_PAYOUT,
        entries=[
            (get_account(withdrawal.user, WalletAccount.Type.LOCKED, withdrawal.currency), -withdrawal.amount),
            (system_account(WalletAccount.Type.CASH, withdrawal.currency), withdrawal.amount),
        ],
        reference=str(withdrawal.id),
        description="Withdrawal paid",
        metadata={"withdrawal_id": str(withdrawal.id), "reference": reference},
        idempotency_key=f"withdrawal:{withdrawal.id}:payout",
    )

    withdrawal.status = Withdrawal.Status.PAID
    withdrawal.paid_at = timezone.now()
    withdrawal.payment_reference = reference
    if proof is not None:
        withdrawal.payment_proof = proof
    withdrawal.save(
        update_fields=["status", "paid_at", "payment_reference", "payment_proof", "updated_at"]
    )

    from apps.automation.services import emit_event

    emit_event("WITHDRAWAL_PAID", withdrawal.user, {"withdrawal_id": str(withdrawal.id)})
    return withdrawal


@transaction.atomic
def reject_withdrawal(withdrawal: Withdrawal, *, reason: str = "", rejected_by=None) -> Withdrawal:
    withdrawal = Withdrawal.objects.select_for_update().get(pk=withdrawal.pk)
    if withdrawal.status in {Withdrawal.Status.PAID, Withdrawal.Status.REJECTED, Withdrawal.Status.CANCELLED}:
        raise WithdrawalError(f"Cannot reject a withdrawal in status '{withdrawal.status}'.")

    txn, _ = ledger.post_transaction(
        type=LedgerTransaction.Type.WITHDRAWAL_REFUND,
        entries=[
            (get_account(withdrawal.user, WalletAccount.Type.LOCKED, withdrawal.currency), -withdrawal.amount),
            (get_account(withdrawal.user, WalletAccount.Type.CASH, withdrawal.currency), withdrawal.amount),
        ],
        reference=str(withdrawal.id),
        description="Withdrawal rejected — funds returned",
        metadata={"withdrawal_id": str(withdrawal.id), "reason": reason},
        idempotency_key=f"withdrawal:{withdrawal.id}:refund",
    )

    withdrawal.status = Withdrawal.Status.REJECTED
    withdrawal.rejection_reason = reason[:255]
    withdrawal.refund_transaction = txn
    withdrawal.save(
        update_fields=["status", "rejection_reason", "refund_transaction", "updated_at"]
    )

    from apps.automation.services import emit_event

    emit_event("WITHDRAWAL_REJECTED", withdrawal.user, {"withdrawal_id": str(withdrawal.id)})
    return withdrawal
