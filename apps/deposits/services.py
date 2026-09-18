"""Deposit services: create payment, confirm and credit the ledger."""
import logging
from datetime import timedelta
from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from apps.ledger import services as ledger
from apps.ledger.models import LedgerTransaction
from apps.payments.models import PaymentProvider, PaymentTransaction
from apps.wallets.models import WalletAccount
from apps.wallets.services import get_account, system_account

from .models import Deposit

logger = logging.getLogger(__name__)

DEFAULT_DEPOSIT_WINDOW_MINUTES = 60

_STATUS_MAP = {
    "waiting": PaymentTransaction.Status.AWAITING_PAYMENT,
    "confirming": PaymentTransaction.Status.CONFIRMING,
    "confirmed": PaymentTransaction.Status.CONFIRMED,
    "finished": PaymentTransaction.Status.CONFIRMED,
    "failed": PaymentTransaction.Status.FAILED,
    "expired": PaymentTransaction.Status.EXPIRED,
    "refunded": PaymentTransaction.Status.REFUNDED,
}


class DepositError(Exception):
    """Raised when a deposit cannot be created or confirmed."""


@transaction.atomic
def create_deposit(*, user, provider: PaymentProvider, amount, currency: str | None = None) -> Deposit:
    from apps.payments.providers.base import load_adapter
    from apps.wallets.services import get_wallet

    amount = Decimal(str(amount))
    if amount <= 0:
        raise DepositError("Deposit amount must be positive.")
    if currency is None:
        currency = get_wallet(user).currency

    deposit = Deposit.objects.create(
        user=user, provider=provider, amount=amount, currency=currency, status=Deposit.Status.CREATED
    )

    adapter = load_adapter(provider)
    created = adapter.create_payment(
        amount=amount, currency=currency, reference=str(deposit.id), user=user
    )

    payment_txn = PaymentTransaction.objects.create(
        provider=provider,
        user=user,
        direction=PaymentTransaction.Direction.DEPOSIT,
        external_id=created.external_id,
        amount=amount,
        currency=currency,
        crypto_amount=created.pay_amount,
        crypto_currency=created.pay_currency,
        status=_STATUS_MAP.get(created.status, PaymentTransaction.Status.CREATED),
        reference=str(deposit.id),
        raw_payload=created.raw,
    )

    deposit.payment_transaction = payment_txn
    deposit.payment_instructions = created.instructions or {"pay_address": created.pay_address}
    deposit.status = Deposit.Status.AWAITING_PAYMENT
    deposit.expires_at = timezone.now() + timedelta(minutes=DEFAULT_DEPOSIT_WINDOW_MINUTES)
    deposit.save(
        update_fields=[
            "payment_transaction",
            "payment_instructions",
            "status",
            "expires_at",
            "updated_at",
        ]
    )
    return deposit


@transaction.atomic
def confirm_deposit(deposit: Deposit, *, raw: dict | None = None) -> Deposit:
    """Credit a confirmed deposit exactly once."""
    deposit = Deposit.objects.select_for_update().get(pk=deposit.pk)

    if deposit.status == Deposit.Status.CONFIRMED:
        return deposit
    if deposit.status in {Deposit.Status.FAILED, Deposit.Status.EXPIRED, Deposit.Status.REFUNDED}:
        raise DepositError(f"Cannot confirm a deposit in status '{deposit.status}'.")

    txn, _ = ledger.post_transaction(
        type=LedgerTransaction.Type.DEPOSIT,
        entries=[
            (system_account(WalletAccount.Type.CASH), -deposit.amount),
            (get_account(deposit.user, WalletAccount.Type.CASH), deposit.amount),
        ],
        reference=str(deposit.id),
        description="Deposit confirmed",
        metadata={"deposit_id": str(deposit.id), "user_id": str(deposit.user_id), "raw": raw or {}},
        idempotency_key=f"deposit:{deposit.id}",
    )

    deposit.status = Deposit.Status.CONFIRMED
    deposit.confirmed_at = timezone.now()
    deposit.credited_at = timezone.now()
    deposit.ledger_transaction = txn
    deposit.save(
        update_fields=["status", "confirmed_at", "credited_at", "ledger_transaction", "updated_at"]
    )

    from apps.automation.services import emit_event

    emit_event("DEPOSIT_CONFIRMED", deposit.user, {"deposit_id": str(deposit.id)})
    return deposit
