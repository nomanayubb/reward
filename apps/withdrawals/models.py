"""Withdrawal methods and withdrawal requests.

The withdrawal lifecycle uses the full state machine from the DRD
(REQUESTED -> UNDER_REVIEW -> APPROVED -> PROCESSING -> PAID / FAILED /
REJECTED / CANCELLED), never a boolean "completed".
"""
from django.conf import settings
from django.db import models

from apps.common.fields import money_field
from apps.common.models import UUIDTimeStampedModel


class WithdrawalMethod(UUIDTimeStampedModel):
    class Type(models.TextChoices):
        EASYPAISA = "easypaisa", "EasyPaisa"
        JAZZCASH = "jazzcash", "JazzCash"
        BANK = "bank", "Bank transfer"
        CRYPTO = "crypto", "Crypto"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="withdrawal_methods"
    )
    type = models.CharField(max_length=16, choices=Type.choices)
    label = models.CharField(max_length=80, blank=True)
    details = models.JSONField(
        default=dict, blank=True,
        help_text="e.g. {'account_number': '03XXXXXXXXX', 'account_name': '...'}",
    )
    is_default = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    disabled_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-is_default", "created_at"]

    def __str__(self):
        return f"{self.type}:{self.user_id}"


class Withdrawal(UUIDTimeStampedModel):
    class Status(models.TextChoices):
        REQUESTED = "requested", "Requested"
        UNDER_REVIEW = "under_review", "Under review"
        APPROVED = "approved", "Approved"
        PROCESSING = "processing", "Processing"
        PAID = "paid", "Paid"
        FAILED = "failed", "Failed"
        REJECTED = "rejected", "Rejected"
        CANCELLED = "cancelled", "Cancelled"

    class Risk(models.TextChoices):
        LOW = "low", "Low"
        MEDIUM = "medium", "Medium"
        HIGH = "high", "High"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="withdrawals"
    )
    method = models.ForeignKey(
        WithdrawalMethod, on_delete=models.PROTECT, related_name="withdrawals"
    )
    payment_provider = models.ForeignKey(
        "payments.PaymentProvider",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="withdrawals",
    )

    amount = money_field()
    fee = money_field()
    net_amount = money_field()
    currency = models.CharField(max_length=16, default="USD")

    status = models.CharField(
        max_length=24, choices=Status.choices, default=Status.REQUESTED, db_index=True
    )
    risk_level = models.CharField(max_length=16, choices=Risk.choices, default=Risk.LOW)

    payout_mode = models.CharField(
        max_length=16, blank=True,
        help_text="auto / manual / hybrid — resolved at request time.",
    )
    requires_dual_approval = models.BooleanField(default=False)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="withdrawals_approved",
    )
    second_approver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="withdrawals_second_approved",
    )

    admin_note = models.CharField(max_length=255, blank=True)
    rejection_reason = models.CharField(max_length=255, blank=True)
    payment_reference = models.CharField(max_length=191, blank=True)
    payment_proof = models.FileField(upload_to="withdrawal_proofs/", null=True, blank=True)

    requested_at = models.DateTimeField(auto_now_add=True, db_index=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    reserve_transaction = models.ForeignKey(
        "ledger.LedgerTransaction",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="withdrawals_reserved",
    )
    payout_transaction = models.ForeignKey(
        "ledger.LedgerTransaction",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="withdrawals_paid",
    )
    refund_transaction = models.ForeignKey(
        "ledger.LedgerTransaction",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="withdrawals_refunded",
    )

    class Meta:
        ordering = ["-requested_at"]
        indexes = [
            models.Index(fields=["status", "requested_at"]),
            models.Index(fields=["user", "status"]),
        ]

    def __str__(self):
        return f"withdrawal:{self.id}:{self.amount} {self.currency}:{self.status}"
