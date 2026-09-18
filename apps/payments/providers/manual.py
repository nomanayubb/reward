"""Manual payment provider adapter (development / manual reconciliation).

Creates a payment with static instructions and never auto-confirms. Enable it
in production only if an admin will confirm payments manually.
"""
from decimal import Decimal

from .base import CreatedPayment, PaymentProviderAdapter, PaymentStatusResult


class ManualProviderAdapter(PaymentProviderAdapter):
    code = "manual"

    def create_payment(self, *, amount, currency: str, reference: str, user=None) -> CreatedPayment:
        return CreatedPayment(
            external_id=f"manual-{reference}",
            status="waiting",
            pay_address="",
            pay_amount=Decimal(str(amount)),
            pay_currency=currency,
            instructions={
                "note": "Manual provider: an admin must confirm this payment.",
                "reference": reference,
                "amount": str(amount),
                "currency": currency,
            },
            raw={"reference": reference, "amount": str(amount), "currency": currency},
        )

    def check_payment(self, external_id: str) -> PaymentStatusResult:
        return PaymentStatusResult(external_id=external_id, status="waiting")

    def verify_webhook(self, payload: dict, headers: dict | None = None) -> bool:
        return False

    def parse_webhook(self, payload: dict, headers: dict | None = None) -> PaymentStatusResult:
        raise NotImplementedError

    def create_payout(self, *, amount, currency: str, destination: dict, reference: str) -> dict:
        raise NotImplementedError
