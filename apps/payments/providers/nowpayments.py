"""NOWPayments adapter (crypto payments).

Implements the provider interface against the NOWPayments API. Credentials
come from the environment (`NOWPAYMENTS_API_KEY`, `NOWPAYMENTS_IPN_SECRET`);
nothing is hard-coded.

STATUS: implemented, **not yet verified against the live/sandbox API** because
no credentials exist in this environment. Before enabling in production:
1. set the env keys,
2. create the `PaymentProvider` row with
   `adapter_path = apps.payments.providers.nowpayments.NowPaymentsAdapter`,
3. run the sandbox checklist in `docs/integrations/NOWPAYMENTS.md`.

IPN (webhook) signature verification is unit-tested and works offline.
"""
import hashlib
import hmac
import json
import urllib.error
import urllib.request
from decimal import Decimal

from django.conf import settings

from apps.payments.services import convert

from .base import (
    CreatedPayment,
    PaymentProviderAdapter,
    PaymentStatusResult,
    ProviderConfigurationError,
    ProviderRequestError,
)

API_BASE = "https://api.nowpayments.io"
SANDBOX_BASE = "https://api-sandbox.nowpayments.io"

STATUS_MAP = {
    "waiting": "awaiting_payment",
    "confirming": "confirming",
    "confirmed": "confirmed",
    "sending": "processing",
    "partially_paid": "confirming",
    "finished": "confirmed",
    "failed": "failed",
    "refunded": "refunded",
    "expired": "expired",
}


def _header(headers: dict | None, name: str) -> str:
    """Case-insensitive header lookup (Django preserves the sent casing)."""
    for key, value in (headers or {}).items():
        if key.lower() == name.lower():
            return str(value)
    return ""


class NowPaymentsAdapter(PaymentProviderAdapter):
    code = "nowpayments"

    @property
    def api_key(self) -> str:
        return getattr(settings, "NOWPAYMENTS_API_KEY", "") or ""

    @property
    def ipn_secret(self) -> str:
        return getattr(settings, "NOWPAYMENTS_IPN_SECRET", "") or ""

    @property
    def base_url(self) -> str:
        if getattr(settings, "NOWPAYMENTS_SANDBOX", True):
            return SANDBOX_BASE
        return API_BASE

    def _request(self, method: str, path: str, body: dict | None = None) -> dict:
        if not self.api_key:
            raise ProviderConfigurationError("NOWPAYMENTS_API_KEY is not configured.")

        request = urllib.request.Request(
            self.base_url + path,
            data=json.dumps(body).encode() if body is not None else None,
            method=method,
        )
        request.add_header("x-api-key", self.api_key)
        request.add_header("Content-Type", "application/json")

        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                return json.loads(response.read().decode("utf-8") or "{}")
        except urllib.error.HTTPError as exc:
            detail = exc.read()[:300]
            raise ProviderRequestError(f"NOWPayments HTTP {exc.code}: {detail!r}") from exc
        except urllib.error.URLError as exc:
            raise ProviderRequestError(f"NOWPayments unreachable: {exc.reason}") from exc

    # -- provider interface -------------------------------------------------
    def create_payment(self, *, amount, currency: str, reference: str, user=None) -> CreatedPayment:
        """Create a crypto invoice. Fiat amounts are converted to USD.

        NOWPayments prices invoices in supported fiat currencies; our wallets
        are PKR-first, so the PKR amount is converted with the admin-set rate
        and the rate used is returned in the payment instructions.
        """
        price_amount = Decimal(str(amount))
        price_currency = (currency or "USD").upper()
        exchange_rate = None

        if price_currency != "USD":
            price_amount, exchange_rate = convert(price_amount, price_currency, "USD")
            price_currency = "USD"

        payload = {
            "price_amount": str(price_amount),
            "price_currency": price_currency.lower(),
            "pay_currency": self.config.get("pay_currency", "usdttrc20"),
            "order_id": reference,
            "order_description": self.config.get("description", "Wallet deposit"),
        }
        ipn_url = self.config.get("ipn_callback_url")
        if ipn_url:
            payload["ipn_callback_url"] = ipn_url

        data = self._request("POST", "/v1/payment", payload)

        instructions = {
            "pay_address": data.get("pay_address", ""),
            "pay_amount": data.get("pay_amount", ""),
            "pay_currency": data.get("pay_currency", ""),
            "price_amount": data.get("price_amount", str(price_amount)),
            "price_currency": data.get("price_currency", price_currency),
        }
        if exchange_rate is not None:
            instructions["exchange_rate_usd_pkr"] = str(exchange_rate)

        return CreatedPayment(
            external_id=str(data.get("payment_id", "")),
            status=str(data.get("payment_status", "waiting")),
            pay_address=data.get("pay_address", ""),
            pay_amount=Decimal(str(data.get("pay_amount", "0") or "0")),
            pay_currency=data.get("pay_currency", ""),
            instructions=instructions,
            raw=data,
        )

    def check_payment(self, external_id: str) -> PaymentStatusResult:
        data = self._request("GET", f"/v1/payment/{external_id}")
        return PaymentStatusResult(
            external_id=str(data.get("payment_id", external_id)),
            status=STATUS_MAP.get(str(data.get("payment_status", "")).lower(), "confirming"),
            amount=Decimal(str(data.get("price_amount", "0") or "0")),
            currency=str(data.get("price_currency", "")).upper(),
            raw=data,
        )

    def verify_webhook(self, payload: dict, headers: dict | None = None) -> bool:
        """HMAC-SHA512 of the alphabetically sorted JSON body, hex digest."""
        secret = self.ipn_secret
        if not secret:
            return False
        signature = _header(headers, "x-nowpayments-sig")
        if not signature:
            return False
        ordered = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        expected = hmac.new(secret.encode(), ordered.encode(), hashlib.sha512).hexdigest()
        return hmac.compare_digest(expected, signature)

    def parse_webhook(self, payload: dict, headers: dict | None = None) -> PaymentStatusResult:
        status = STATUS_MAP.get(
            str(payload.get("payment_status", "")).lower(), "confirming"
        )
        return PaymentStatusResult(
            external_id=str(payload.get("payment_id", "")),
            status=status,
            amount=Decimal(str(payload.get("price_amount", "0") or "0")),
            currency=str(payload.get("price_currency", "")).upper(),
            raw=payload,
        )

    def create_payout(self, *, amount, currency: str, destination: dict, reference: str) -> dict:
        """Payout automation is intentionally not enabled yet.

        NOWPayments payouts require a verified payout API setup (2FA and
        payout wallet verification). Until that is confirmed, withdrawals are
        paid manually by admins and this method refuses to fabricate a payout.
        """
        raise NotImplementedError(
            "NOWPayments payouts are not enabled; complete payout API verification first."
        )
