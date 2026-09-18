"""Exchange-rate conversion tests (ADR-015 slice 2)."""
from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError

from apps.adminpanel.settings import set_setting
from apps.payments.services import convert, usd_to_pkr_rate

pytestmark = pytest.mark.django_db


def test_default_rate_is_used_for_usd_to_pkr():
    converted, rate = convert(Decimal("1.00"), "USD", "PKR")

    assert rate == Decimal("280.00")
    assert converted == Decimal("280.00000000")


def test_default_rate_is_used_for_pkr_to_usd():
    converted, rate = convert(Decimal("280.00"), "PKR", "USD")

    assert rate == Decimal("280.00")
    assert converted == Decimal("1.00000000")


def test_same_currency_is_passthrough():
    converted, rate = convert(Decimal("12.34"), "PKR", "PKR")

    assert converted == Decimal("12.34000000")
    assert rate == Decimal("1")


def test_explicit_rate_overrides_setting():
    converted, rate = convert(Decimal("1.00"), "USD", "PKR", rate=Decimal("300.00"))

    assert converted == Decimal("300.00000000")
    assert rate == Decimal("300.00")


def test_admin_setting_changes_the_rate():
    set_setting("EXCHANGE_RATE_USD_PKR", "310.00", group="payments")

    assert usd_to_pkr_rate() == Decimal("310.00")
    converted, _ = convert(Decimal("2.00"), "USD", "PKR")
    assert converted == Decimal("620.00000000")


def test_unknown_currency_pair_is_rejected():
    with pytest.raises(ValidationError):
        convert(Decimal("1.00"), "USD", "EUR")
