"""Multi-currency wallet and ledger integrity tests (ADR-015 slice 1)."""
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from apps.ledger.models import LedgerTransaction
from apps.ledger.services import post_transaction
from apps.wallets.models import WalletAccount
from apps.wallets.services import get_account, get_wallet, system_account

pytestmark = pytest.mark.django_db

STRONG_PASSWORD = "StrongPass123!"


@pytest.fixture
def user():
    account = get_user_model().objects.create_user(
        email="multi@example.com", password=STRONG_PASSWORD
    )
    get_wallet(account)
    return account


def test_accounts_can_be_provisioned_per_currency(user):
    pkr_cash = get_account(user, WalletAccount.Type.CASH, "PKR")
    usd_cash = get_account(user, WalletAccount.Type.CASH, "USD")

    assert pkr_cash.pk != usd_cash.pk
    assert pkr_cash.currency == "PKR"
    assert usd_cash.currency == "USD"


def test_balanced_multi_currency_transaction_is_allowed(user):
    entries = [
        (system_account(WalletAccount.Type.CASH, "USD"), Decimal("-5.00")),
        (get_account(user, WalletAccount.Type.CASH, "USD"), Decimal("5.00")),
        (system_account(WalletAccount.Type.CASH, "PKR"), Decimal("-1400.00")),
        (get_account(user, WalletAccount.Type.CASH, "PKR"), Decimal("1400.00")),
    ]

    _, created = post_transaction(
        type=LedgerTransaction.Type.ADJUSTMENT, entries=entries, idempotency_key="multi-ok"
    )

    assert created is True
    assert get_account(user, WalletAccount.Type.CASH, "USD").balance == Decimal("5.00")
    assert get_account(user, WalletAccount.Type.CASH, "PKR").balance == Decimal("1400.00")


def test_cross_currency_leak_is_rejected(user):
    """USD out and PKR in nets to zero overall but is unbalanced in both."""
    entries = [
        (get_account(user, WalletAccount.Type.CASH, "USD"), Decimal("-5.00")),
        (get_account(user, WalletAccount.Type.CASH, "PKR"), Decimal("5.00")),
    ]

    with pytest.raises(ValidationError):
        post_transaction(
            type=LedgerTransaction.Type.ADJUSTMENT, entries=entries, idempotency_key="leak"
        )


def test_currency_balances_are_independent(user):
    post_transaction(
        type=LedgerTransaction.Type.ADJUSTMENT,
        entries=[
            (system_account(WalletAccount.Type.CASH, "USD"), Decimal("-3.00")),
            (get_account(user, WalletAccount.Type.CASH, "USD"), Decimal("3.00")),
        ],
        idempotency_key="usd-only",
    )
    post_transaction(
        type=LedgerTransaction.Type.ADJUSTMENT,
        entries=[
            (system_account(WalletAccount.Type.CASH, "PKR"), Decimal("-900.00")),
            (get_account(user, WalletAccount.Type.CASH, "PKR"), Decimal("900.00")),
        ],
        idempotency_key="pkr-only",
    )

    assert get_account(user, WalletAccount.Type.CASH, "USD").balance == Decimal("3.00")
    assert get_account(user, WalletAccount.Type.CASH, "PKR").balance == Decimal("900.00")
