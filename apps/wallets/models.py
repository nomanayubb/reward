"""Wallets and wallet accounts.

A wallet groups the separate ledgers a user owns. ``WalletAccount.balance`` is
a cached representation of the immutable ledger — it must only ever be updated
through ``apps.ledger.services`` inside a transaction with row locking.
"""
from decimal import Decimal

from django.conf import settings
from django.db import models

from apps.common.fields import money_field
from apps.common.models import UUIDTimeStampedModel


class Wallet(UUIDTimeStampedModel):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="wallet"
    )
    currency = models.CharField(max_length=8, default="USD")
    is_locked = models.BooleanField(default=False)
    lock_reason = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"wallet:{self.user_id}"

    def account(self, account_type: str, currency: str | None = None):
        return self.accounts.get(type=account_type, currency=currency or self.currency)


class WalletAccount(UUIDTimeStampedModel):
    class Type(models.TextChoices):
        CASH = "cash", "Cash"
        POINTS = "points", "Points"
        BONUS = "bonus", "Bonus"
        PENDING = "pending", "Pending"
        LOCKED = "locked", "Locked"
        WITHDRAWABLE = "withdrawable", "Withdrawable"
        DEPOSIT = "deposit", "Deposit"

    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name="accounts")
    type = models.CharField(max_length=16, choices=Type.choices)
    currency = models.CharField(max_length=8, default="USD")
    balance = money_field()
    is_frozen = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["wallet", "type", "currency"], name="uniq_wallet_account"
            )
        ]
        indexes = [models.Index(fields=["type", "currency"])]

    def __str__(self):
        return f"{self.type}:{self.balance} {self.currency}"

    @property
    def available(self) -> Decimal:
        if self.is_frozen:
            return Decimal("0")
        return self.balance


class BalanceSnapshot(UUIDTimeStampedModel):
    """Point-in-time copy of an account balance for auditing/reporting."""

    account = models.ForeignKey(
        WalletAccount, on_delete=models.CASCADE, related_name="snapshots"
    )
    balance = money_field()
    reason = models.CharField(max_length=64, blank=True)
    taken_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-taken_at"]

    def __str__(self):
        return f"snapshot:{self.account_id}:{self.balance}"
