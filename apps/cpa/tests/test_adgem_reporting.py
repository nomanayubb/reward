"""AdGem reporting client + reconciliation tests."""
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import override_settings

from apps.cpa.models import CPAProvider
from apps.cpa.providers.adgem import AdgemAdapter
from apps.offers.models import Offer, OfferConversion
from apps.offers.reconciliation import reconcile_provider
from apps.wallets.services import get_wallet

pytestmark = pytest.mark.django_db


@pytest.fixture
def provider():
    return CPAProvider.objects.create(
        code="adgem",
        name="AdGem",
        adapter_path="apps.cpa.providers.adgem.AdgemAdapter",
        is_enabled=True,
        config={},
    )


@pytest.fixture
def adapter(provider):
    return AdgemAdapter(provider)


@override_settings(ADGEM_REPORT_TOKEN="report-token")
def test_get_reporting_data_returns_rows(adapter, monkeypatch):
    captured = {}

    def fake_report_request(params):
        captured["params"] = params
        return [{"app_id": 1, "date": "2026-09-01", "conversions": 3, "payout": 4.5}]

    monkeypatch.setattr(adapter, "_report_request", fake_report_request)

    rows = adapter.get_reporting_data()

    assert rows[0]["conversions"] == 3
    assert ("group_by[]", "app_id") in captured["params"]


@override_settings(ADGEM_REPORT_TOKEN="", ADGEM_API_KEY="")
def test_reporting_without_token_raises(adapter):
    from apps.cpa.providers.base import ProviderConfigurationError

    with pytest.raises(ProviderConfigurationError):
        adapter.get_reporting_data()


def _local_conversion(provider, user, reference: str, payout: str):
    offer = Offer.objects.create(
        provider=provider,
        external_id=f"offer-{reference}",
        title="Recon offer",
        payout=Decimal(payout),
        user_reward=Decimal("0"),
    )
    return OfferConversion.objects.create(
        user=user,
        offer=offer,
        provider=provider,
        external_conversion_id=reference,
        payout=Decimal(payout),
        user_reward=Decimal("0"),
        status=OfferConversion.Status.APPROVED,
    )


def test_reconcile_provider_reports_differences(provider, monkeypatch):
    user = get_user_model().objects.create_user(
        email="recon@example.com", password="StrongPass123!"
    )
    get_wallet(user)
    _local_conversion(provider, user, "c1", "1.00")

    class FakeAdapter:
        def get_reporting_data(self, since=None, until=None):
            return [{"conversions": 2, "payout": 3.0}]

    monkeypatch.setattr("apps.cpa.providers.base.load_adapter", lambda p: FakeAdapter())

    result = reconcile_provider(provider, days=7)

    assert result.reported_conversions == 2
    assert result.local_conversions == 1
    assert result.conversion_difference == 1
    assert result.reported_payout == Decimal("3.0")
    assert result.local_payout == Decimal("1.00")
    assert result.payout_difference == Decimal("2.00")
    assert result.is_balanced is False


def test_reconcile_command_outputs_summary(provider, monkeypatch, capsys):
    class FakeAdapter:
        def get_reporting_data(self, since=None, until=None):
            return []

    monkeypatch.setattr("apps.cpa.providers.base.load_adapter", lambda p: FakeAdapter())

    call_command("reconcile_provider", "adgem", "--days", "7")

    output = capsys.readouterr().out
    assert "Reported conversions: 0" in output
    assert "Balanced" in output
