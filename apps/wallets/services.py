"""Wallet services: wallet/account provisioning and system accounts."""
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db import transaction

from .models import BalanceSnapshot, Wallet, WalletAccount

POINTS_CURRENCY = "POINTS"

# Currencies a wallet may hold (ADR-015: PKR primary, USD for crypto).
SUPPORTED_CURRENCIES = ("PKR", "USD")
PRIMARY_CURRENCY = "PKR"

DEFAULT_ACCOUNT_TYPES = [
    WalletAccount.Type.CASH,
    WalletAccount.Type.BONUS,
    WalletAccount.Type.PENDING,
    WalletAccount.Type.LOCKED,
    WalletAccount.Type.WITHDRAWABLE,
    WalletAccount.Type.DEPOSIT,
]

SYSTEM_USER_EMAIL = "system@reward-platform.local"


@transaction.atomic
def get_wallet(user) -> Wallet:
    wallet, _ = Wallet.objects.get_or_create(user=user, defaults={"currency": PRIMARY_CURRENCY})
    ensure_accounts(wallet)
    return wallet


@transaction.atomic
def ensure_accounts(wallet: Wallet, currency: str | None = None) -> dict[str, WalletAccount]:
    currency = currency or wallet.currency
    accounts: dict[str, WalletAccount] = {}
    for account_type in DEFAULT_ACCOUNT_TYPES:
        account, _ = WalletAccount.objects.get_or_create(
            wallet=wallet, type=account_type, currency=currency
        )
        accounts[account_type] = account
    points, _ = WalletAccount.objects.get_or_create(
        wallet=wallet, type=WalletAccount.Type.POINTS, currency=POINTS_CURRENCY
    )
    accounts[WalletAccount.Type.POINTS] = points
    return accounts


def get_account(user, account_type: str, currency: str | None = None) -> WalletAccount:
    """Fetch (or provision) one account for a user in a given currency."""
    wallet = get_wallet(user)
    currency = currency or wallet.currency
    account, _ = WalletAccount.objects.get_or_create(
        wallet=wallet, type=account_type, currency=currency
    )
    return account


@transaction.atomic
def get_system_wallet() -> Wallet:
    """Platform-side wallet used as the counterparty for user movements."""
    User = get_user_model()
    user, _ = User.objects.get_or_create(
        email=SYSTEM_USER_EMAIL,
        defaults={"username": "system", "is_active": False, "status": "inactive"},
    )
    return get_wallet(user)


def system_account(account_type: str, currency: str = "USD") -> WalletAccount:
    wallet = get_system_wallet()
    account, _ = WalletAccount.objects.get_or_create(
        wallet=wallet, type=account_type, currency=currency
    )
    return account


def points_account(user) -> WalletAccount:
    wallet = get_wallet(user)
    account, _ = WalletAccount.objects.get_or_create(
        wallet=wallet, type=WalletAccount.Type.POINTS, currency=POINTS_CURRENCY
    )
    return account


def system_points_account() -> WalletAccount:
    wallet = get_system_wallet()
    account, _ = WalletAccount.objects.get_or_create(
        wallet=wallet, type=WalletAccount.Type.POINTS, currency=POINTS_CURRENCY
    )
    return account


def system_pending_points_account() -> WalletAccount:
    """Holding account for points awarded but not yet approved."""
    wallet = get_system_wallet()
    account, _ = WalletAccount.objects.get_or_create(
        wallet=wallet, type=WalletAccount.Type.PENDING, currency=POINTS_CURRENCY
    )
    return account


def snapshot(account: WalletAccount, reason: str = "") -> BalanceSnapshot:
    return BalanceSnapshot.objects.create(account=account, balance=account.balance, reason=reason)


def total_liability(currency: str = "USD") -> Decimal:
    """Sum of user-owed balances (cash + locked + withdrawable + pending)."""
    from django.db.models import Sum

    liability_types = [
        WalletAccount.Type.CASH,
        WalletAccount.Type.LOCKED,
        WalletAccount.Type.WITHDRAWABLE,
        WalletAccount.Type.PENDING,
    ]
    total = (
        WalletAccount.objects.filter(type__in=liability_types, currency=currency)
        .exclude(wallet__user__email=SYSTEM_USER_EMAIL)
        .aggregate(total=Sum("balance"))["total"]
    )
    return total or Decimal("0")


@transaction.atomic
def adjust_balance(*, user, amount, currency: str = "PKR", reason: str = "", actor=None):
    """Admin balance adjustment: positive credits, negative debits.

    Always creates an immutable ledger transaction; callers must also write an
    audit-log entry with the reason (DRD §56).
    """
    from apps.ledger import services as ledger
    from apps.ledger.models import LedgerTransaction

    amount = Decimal(str(amount))
    if amount == 0:
        raise ValueError("Adjustment amount must not be zero.")

    account = get_account(user, WalletAccount.Type.CASH, currency)
    counterpart = system_account(WalletAccount.Type.CASH, currency)

    txn, _ = ledger.post_transaction(
        type=LedgerTransaction.Type.ADJUSTMENT,
        entries=[(counterpart, -amount), (account, amount)],
        reference=f"admin-adjustment:{user.pk}",
        description=reason or "Admin balance adjustment",
        metadata={
            "user_id": str(user.pk),
            "actor_id": str(getattr(actor, "pk", "")) if actor else "",
            "reason": reason,
        },
    )
    return txn
