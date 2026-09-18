"""Wallet services: wallet/account provisioning and system accounts."""
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db import transaction

from .models import BalanceSnapshot, Wallet, WalletAccount

DEFAULT_ACCOUNT_TYPES = [
    WalletAccount.Type.CASH,
    WalletAccount.Type.POINTS,
    WalletAccount.Type.BONUS,
    WalletAccount.Type.PENDING,
    WalletAccount.Type.LOCKED,
    WalletAccount.Type.WITHDRAWABLE,
    WalletAccount.Type.DEPOSIT,
]

SYSTEM_USER_EMAIL = "system@reward-platform.local"


@transaction.atomic
def get_wallet(user) -> Wallet:
    wallet, _ = Wallet.objects.get_or_create(user=user, defaults={"currency": "USD"})
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
    return accounts


def get_account(user, account_type: str, currency: str | None = None) -> WalletAccount:
    wallet = get_wallet(user)
    return WalletAccount.objects.get(
        wallet=wallet, type=account_type, currency=currency or wallet.currency
    )


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
    return WalletAccount.objects.get(wallet=wallet, type=account_type, currency=currency)


POINTS_CURRENCY = "POINTS"


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
