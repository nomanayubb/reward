"""Payment providers (NOWPayments, EasyPaisa, ...) and payment transactions.

Provider-specific logic lives in adapters (``apps/payments/providers/``), never
in views. ``PaymentProvider`` rows are admin configuration.
"""
from django.conf import settings
from django.db import models

from apps.common.fields import money_field
from apps.common.models import UUIDTimeStampedModel


class PaymentProvider(UUIDTimeStampedModel):
    class Kind(models.TextChoices):
        CRYPTO = "crypto", "Crypto"
        LOCAL = "local", "Local / Bank / Wallet"
        CARD = "card", "Card"

    class Health(models.TextChoices):
        HEALTHY = "healthy", "Healthy"
        DEGRADED = "degraded", "Degraded"
        DOWN = "down", "Down"
        UNKNOWN = "unknown", "Unknown"

    code = models.CharField(max_length=64, unique=True, help_text="e.g. nowpayments")
    name = models.CharField(max_length=120)
    kind = models.CharField(max_length=16, choices=Kind.choices)
    is_enabled = models.BooleanField(default=False, db_index=True)
    supports_deposits = models.BooleanField(default=True)
    supports_withdrawals = models.BooleanField(default=False)

    config = models.JSONField(
        default=dict, blank=True,
        help_text="Non-secret settings. Secrets come from environment variables.",
    )
    fee_percentage = models.DecimalField(max_digits=6, decimal_places=3, default=0)
    fee_fixed = money_field()

    health = models.CharField(max_length=16, choices=Health.choices, default=Health.UNKNOWN)
    last_health_check_at = models.DateTimeField(null=True, blank=True)
    last_error = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.code})"


class PaymentTransaction(UUIDTimeStampedModel):
    class Direction(models.TextChoices):
        DEPOSIT = "deposit", "Deposit"
        WITHDRAWAL = "withdrawal", "Withdrawal"

    class Status(models.TextChoices):
        CREATED = "created", "Created"
        AWAITING_PAYMENT = "awaiting_payment", "Awaiting payment"
        DETECTED = "detected", "Detected"
        CONFIRMING = "confirming", "Confirming"
        CONFIRMED = "confirmed", "Confirmed"
        PROCESSING = "processing", "Processing"
        PAID = "paid", "Paid"
        FAILED = "failed", "Failed"
        EXPIRED = "expired", "Expired"
        REFUNDED = "refunded", "Refunded"
        CANCELLED = "cancelled", "Cancelled"

    provider = models.ForeignKey(
        PaymentProvider, on_delete=models.PROTECT, related_name="transactions"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="payment_transactions"
    )
    direction = models.CharField(max_length=16, choices=Direction.choices, db_index=True)

    external_id = models.CharField(max_length=191, db_index=True)
    amount = money_field()
    currency = models.CharField(max_length=16, default="USD")
    crypto_amount = money_field(null=True, blank=True)
    crypto_currency = models.CharField(max_length=16, blank=True)
    exchange_rate = models.DecimalField(max_digits=24, decimal_places=12, null=True, blank=True)

    status = models.CharField(
        max_length=24, choices=Status.choices, default=Status.CREATED, db_index=True
    )
    reference = models.CharField(max_length=128, blank=True, db_index=True)
    raw_payload = models.JSONField(default=dict, blank=True)
    error_message = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["provider", "external_id"], name="uniq_provider_external_id"
            )
        ]
        indexes = [
            models.Index(fields=["status", "direction", "created_at"]),
        ]

    def __str__(self):
        return f"{self.provider_id}:{self.external_id}:{self.status}"
