"""Immutable double-entry ledger.

Rules (see docs/DRD.md §6, §105-106):
- Entries are never updated or deleted. Corrections are REVERSAL transactions.
- Every transaction's entries must sum to zero (enforced in services).
- ``idempotency_key`` makes external events (postbacks) safe to replay.
- Wallet balances are derived from these entries, not the source of truth.
"""
from django.core.exceptions import ValidationError
from django.db import models

from apps.common.fields import money_field
from apps.common.models import UUIDModel, UUIDTimeStampedModel


class LedgerTransaction(UUIDTimeStampedModel):
    class Type(models.TextChoices):
        REWARD = "reward", "Reward"
        REVERSAL = "reversal", "Reversal"
        BONUS = "bonus", "Bonus"
        DEPOSIT = "deposit", "Deposit"
        WITHDRAWAL_RESERVE = "withdrawal_reserve", "Withdrawal reserve"
        WITHDRAWAL_PAYOUT = "withdrawal_payout", "Withdrawal payout"
        WITHDRAWAL_REFUND = "withdrawal_refund", "Withdrawal refund"
        ADJUSTMENT = "adjustment", "Admin adjustment"
        FEE = "fee", "Fee"
        CONVERSION = "conversion", "Conversion"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        POSTED = "posted", "Posted"
        REVERSED = "reversed", "Reversed"

    type = models.CharField(max_length=32, choices=Type.choices, db_index=True)
    status = models.CharField(
        max_length=16, choices=Status.choices, default=Status.POSTED, db_index=True
    )
    reference = models.CharField(max_length=128, blank=True, db_index=True)
    description = models.CharField(max_length=255, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    idempotency_key = models.CharField(
        max_length=191,
        unique=True,
        null=True,
        blank=True,
        help_text="Unique external key, e.g. 'cpa:networkA:conversion123'.",
    )

    reverses = models.OneToOneField(
        "self",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="reversed_by",
    )

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["type", "status", "created_at"]),
        ]

    def __str__(self):
        return f"txn:{self.id}:{self.type}:{self.status}"


class LedgerEntry(UUIDModel):
    transaction = models.ForeignKey(
        LedgerTransaction, on_delete=models.PROTECT, related_name="entries"
    )
    account = models.ForeignKey(
        "wallets.WalletAccount", on_delete=models.PROTECT, related_name="entries"
    )
    amount = money_field(help_text="Signed amount: positive credits the account.")
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["account", "created_at"]),
        ]

    def __str__(self):
        return f"entry:{self.account_id}:{self.amount}"

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValidationError("Ledger entries are immutable; create a reversal instead.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Ledger entries cannot be deleted; create a reversal instead.")
