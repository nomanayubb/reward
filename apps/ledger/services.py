"""Ledger services — the ONLY code allowed to move wallet balances.

Every financial movement is a balanced, immutable, idempotent transaction.
Views/tasks must call these helpers, never touch ``WalletAccount.balance``.
"""
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models import Sum

from apps.wallets.models import WalletAccount

from .models import LedgerEntry, LedgerTransaction


class LedgerError(ValidationError):
    """Raised when a ledger operation would break accounting invariants."""


@transaction.atomic
def post_transaction(
    *,
    type: str,
    entries: list[tuple[WalletAccount, Decimal]],
    reference: str = "",
    description: str = "",
    metadata: dict | None = None,
    idempotency_key: str | None = None,
    status: str = LedgerTransaction.Status.POSTED,
) -> tuple[LedgerTransaction, bool]:
    """Post a balanced double-entry transaction.

    ``entries`` is a list of ``(WalletAccount, signed_amount)`` pairs and must
    sum to zero. Returns ``(transaction, created)``; when ``idempotency_key``
    was already used the existing transaction is returned with ``created=False``.
    """
    if not entries:
        raise LedgerError("A ledger transaction needs at least one entry pair.")

    if idempotency_key:
        existing = LedgerTransaction.objects.filter(idempotency_key=idempotency_key).first()
        if existing:
            return existing, False

    total = sum((amount for _, amount in entries), Decimal("0"))
    if total != 0:
        raise LedgerError(f"Ledger entries must sum to zero, got {total}.")

    # Multi-currency safety: every currency present in the transaction must
    # balance on its own. This permits balanced multi-currency movements while
    # making cross-currency leakage impossible.
    totals: dict[str, Decimal] = {}
    for account, amount in entries:
        totals[account.currency] = totals.get(account.currency, Decimal("0")) + amount
    unbalanced = {currency: total for currency, total in totals.items() if total != 0}
    if unbalanced:
        raise LedgerError(f"Ledger entries must sum to zero per currency, got {unbalanced}.")

    account_ids = {account.pk for account, _ in entries}
    locked = {
        account.pk: account
        for account in WalletAccount.objects.select_for_update().filter(pk__in=account_ids)
    }
    if len(locked) != len(account_ids):
        raise LedgerError("Unknown wallet account referenced in ledger entries.")

    try:
        txn = LedgerTransaction.objects.create(
            type=type,
            status=status,
            reference=reference,
            description=description,
            metadata=metadata or {},
            idempotency_key=idempotency_key,
        )
    except IntegrityError:
        existing = LedgerTransaction.objects.filter(idempotency_key=idempotency_key).first()
        if existing:
            return existing, False
        raise

    for account, amount in entries:
        locked_account = locked[account.pk]
        LedgerEntry.objects.create(transaction=txn, account=locked_account, amount=amount)
        locked_account.balance = locked_account.balance + amount
        locked_account.save(update_fields=["balance", "updated_at"])

    return txn, True


@transaction.atomic
def reverse_transaction(
    txn: LedgerTransaction, *, reason: str = ""
) -> tuple[LedgerTransaction, bool]:
    """Create the compensating transaction for ``txn`` (never edit history)."""
    if txn.status == LedgerTransaction.Status.REVERSED:
        reversal = getattr(txn, "reversed_by", None)
        if reversal:
            return reversal, False

    entries = [(entry.account, -entry.amount) for entry in txn.entries.select_related("account")]
    reversal, created = post_transaction(
        type=LedgerTransaction.Type.REVERSAL,
        entries=entries,
        reference=txn.reference,
        description=reason or f"Reversal of {txn.id}",
        metadata={"reverses": str(txn.id)},
        idempotency_key=f"reversal:{txn.id}",
    )
    if created:
        txn.status = LedgerTransaction.Status.REVERSED
        txn.reversed_by = reversal
        txn.save(update_fields=["status", "updated_at"])
    return reversal, created


def account_balance(account: WalletAccount) -> Decimal:
    """Balance computed from the ledger (source of truth)."""
    total = LedgerEntry.objects.filter(account=account).aggregate(total=Sum("amount"))["total"]
    return total or Decimal("0")


def verify_account_balance(account: WalletAccount) -> bool:
    """True when the cached balance matches the ledger."""
    return account_balance(account) == account.balance
