"""Deposits — user funding via crypto or local payment methods."""
from django.conf import settings
from django.db import models

from apps.common.fields import money_field
from apps.common.models import UUIDTimeStampedModel


class Deposit(UUIDTimeStampedModel):
    class Status(models.TextChoices):
        CREATED = "created", "Created"
        AWAITING_PAYMENT = "awaiting_payment", "Awaiting payment"
        PAYMENT_DETECTED = "payment_detected", "Payment detected"
        CONFIRMING = "confirming", "Confirming"
        CONFIRMED = "confirmed", "Confirmed"
        FAILED = "failed", "Failed"
        EXPIRED = "expired", "Expired"
        REFUNDED = "refunded", "Refunded"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="deposits"
    )
    provider = models.ForeignKey(
        "payments.PaymentProvider", on_delete=models.PROTECT, related_name="deposits"
    )
    payment_transaction = models.ForeignKey(
        "payments.PaymentTransaction",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="deposits",
    )

    amount = money_field()
    currency = models.CharField(max_length=16, default="USD")
    status = models.CharField(
        max_length=24, choices=Status.choices, default=Status.CREATED, db_index=True
    )

    payment_instructions = models.JSONField(default=dict, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    credited_at = models.DateTimeField(null=True, blank=True)

    ledger_transaction = models.ForeignKey(
        "ledger.LedgerTransaction",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="deposits",
    )

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "status", "created_at"]),
            models.Index(fields=["status", "expires_at"]),
        ]

    def __str__(self):
        return f"deposit:{self.id}:{self.amount} {self.currency}:{self.status}"
