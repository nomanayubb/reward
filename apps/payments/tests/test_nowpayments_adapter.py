"""NOWPayments adapter tests: signature verification, parsing, invoice creation."""
import hashlib
import hmac
import json
from decimal import Decimal

import pytest
from django.test import override_settings

from apps.payments.models import PaymentProvider
from apps.payments.providers.base import ProviderConfigurationError
from apps.payments.providers.nowpayments import NowPaymentsAdapter

pytestmark = pytest.mark.django_db


@pytest.fixture
def provider():
    return PaymentProvider.objects.create(
        code="nowpayments",
        name="NOWPayments",
        kind=PaymentProvider.Kind.CRYPTO,
        is_enabled=True,
        supports_deposits=True,
        config={"adapter_path": "apps.payments.providers.nowpayments.NowPaymentsAdapter"},
    )


@pytest.fixture
def adapter(provider):
    return NowPaymentsAdapter(provider)


def _sign(payload: dict, secret: str) -> str:
    ordered = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hmac.new(secret.encode(), ordered.encode(), hashlib.sha512).hexdigest()


@override_settings(NOWPAYMENTS_IPN_SECRET="test-ipn-secret")
def test_verify_webhook_accepts_valid_signature(adapter):
    payload = {"payment_id": "123", "payment_status": "finished", "price_amount": 10}
    signature = _sign(payload, "test-ipn-secret")

    assert adapter.verify_webhook(payload, {"x-nowpayments-sig": signature}) is True


@override_settings(NOWPAYMENTS_IPN_SECRET="test-ipn-secret")
def test_verify_webhook_rejects_tampered_payload(adapter):
    payload = {"payment_id": "123", "payment_status": "finished"}
    signature = _sign(payload, "test-ipn-secret")
    tampered = {**payload, "payment_status": "failed"}

    assert adapter.verify_webhook(tampered, {"x-nowpayments-sig": signature}) is False


@override_settings(NOWPAYMENTS_IPN_SECRET="")
def test_verify_webhook_without_secret_is_false(adapter):
    assert adapter.verify_webhook({"a": 1}, {"x-nowpayments-sig": "whatever"}) is False


def test_parse_webhook_maps_status(adapter):
    result = adapter.parse_webhook(
        {
            "payment_id": "42",
            "payment_status": "finished",
            "price_amount": "10.5",
            "price_currency": "usd",
        }
    )

    assert result.external_id == "42"
    assert result.status == "confirmed"
    assert result.amount == Decimal("10.5")
    assert result.currency == "USD"


def test_parse_webhook_unknown_status_defaults_to_confirming(adapter):
    result = adapter.parse_webhook({"payment_id": "1", "payment_status": "mystery"})

    assert result.status == "confirming"


@override_settings(NOWPAYMENTS_API_KEY="")
def test_create_payment_without_api_key_raises(adapter):
    with pytest.raises(ProviderConfigurationError):
        adapter.create_payment(amount=Decimal("1000"), currency="PKR", reference="ref-1")


@override_settings(NOWPAYMENTS_API_KEY="test-key", NOWPAYMENTS_SANDBOX=True)
def test_create_payment_converts_pkr_to_usd(adapter, monkeypatch):
    captured = {}

    def fake_request(method, path, body=None):
        captured["method"] = method
        captured["path"] = path
        captured["body"] = body
        return {
            "payment_id": 987654,
            "payment_status": "waiting",
            "pay_address": "TXYZ",
            "pay_amount": 10.05,
            "pay_currency": "usdttrc20",
            "price_amount": 10,
            "price_currency": "usd",
        }

    monkeypatch.setattr(adapter, "_request", fake_request)

    created = adapter.create_payment(amount=Decimal("2800"), currency="PKR", reference="dep-1")

    assert captured["method"] == "POST"
    assert captured["path"] == "/v1/payment"
    assert captured["body"]["price_amount"] == "10.00000000"
    assert captured["body"]["price_currency"] == "usd"
    assert captured["body"]["order_id"] == "dep-1"
    assert created.external_id == "987654"
    assert created.pay_address == "TXYZ"
    assert created.instructions["exchange_rate_usd_pkr"] == "280.00"


@override_settings(NOWPAYMENTS_API_KEY="test-key", NOWPAYMENTS_SANDBOX=True)
def test_check_payment_maps_status(adapter, monkeypatch):
    monkeypatch.setattr(
        adapter,
        "_request",
        lambda method, path, body=None: {
            "payment_id": 5,
            "payment_status": "finished",
            "price_amount": 3,
            "price_currency": "usd",
        },
    )

    result = adapter.check_payment("5")

    assert result.status == "confirmed"
    assert result.amount == Decimal("3")
