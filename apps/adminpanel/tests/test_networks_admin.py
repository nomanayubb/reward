"""Multi-network admin console tests: tabs, adding networks, connection tests."""
import pytest
from django.contrib.auth import get_user_model
from django.test import Client

from apps.adminpanel.models import AuditLog
from apps.cpa.models import CPAProvider
from apps.payments.models import PaymentProvider
from apps.wallets.services import get_wallet

pytestmark = pytest.mark.django_db

STRONG_PASSWORD = "StrongPass123!"


@pytest.fixture
def staff():
    account = get_user_model().objects.create_user(
        email="networks-staff@example.com", password=STRONG_PASSWORD, is_staff=True
    )
    get_wallet(account)
    return account


@pytest.fixture
def client():
    return Client()


def test_tabs_render(client, staff):
    client.force_login(staff)

    response = client.get("/admin-panel/providers/?tab=cpa")

    assert response.status_code == 200
    assert b"CPA networks" in response.content
    assert b"Add network" in response.content


def test_overview_tab_shows_switches(client, staff):
    client.force_login(staff)

    response = client.get("/admin-panel/providers/")

    assert response.status_code == 200
    assert b"Emergency switches" in response.content


def test_add_cpa_network(client, staff):
    client.force_login(staff)

    response = client.post(
        "/admin-panel/providers/action/",
        {
            "action": "add_network",
            "kind": "cpa",
            "code": "adgem",
            "name": "AdGem",
            "adapter_path": "apps.cpa.providers.adgem.AdGemAdapter",
            "priority": "50",
            "config": '{"feed_url": "https://api.example/offers"}',
            "is_enabled": "on",
        },
    )

    assert response.status_code == 302
    provider = CPAProvider.objects.get(code="adgem")
    assert provider.priority == 50
    assert provider.config["feed_url"] == "https://api.example/offers"
    assert provider.is_enabled is True
    assert AuditLog.objects.filter(action="network.create").exists()


def test_add_payment_network_moves_adapter_path_into_config(client, staff):
    client.force_login(staff)

    client.post(
        "/admin-panel/providers/action/",
        {
            "action": "add_network",
            "kind": "payment",
            "code": "np2",
            "name": "NOWPayments 2",
            "adapter_path": "apps.payments.providers.nowpayments.NowPaymentsAdapter",
            "priority": "100",
            "config": "",
            "payment_kind": "crypto",
            "supports_deposits": "on",
        },
    )

    provider = PaymentProvider.objects.get(code="np2")
    assert provider.kind == PaymentProvider.Kind.CRYPTO
    assert provider.supports_deposits is True
    assert provider.config["adapter_path"].endswith("NowPaymentsAdapter")


def test_invalid_config_json_is_rejected(client, staff):
    client.force_login(staff)

    client.post(
        "/admin-panel/providers/action/",
        {
            "action": "add_network",
            "kind": "cpa",
            "code": "broken",
            "name": "Broken",
            "adapter_path": "",
            "priority": "100",
            "config": "{not json",
        },
    )

    assert not CPAProvider.objects.filter(code="broken").exists()


def test_test_action_reports_missing_nowpayments_credentials(client, staff):
    provider = PaymentProvider.objects.create(
        code="nowpayments",
        name="NOWPayments",
        kind=PaymentProvider.Kind.CRYPTO,
        is_enabled=True,
        config={"adapter_path": "apps.payments.providers.nowpayments.NowPaymentsAdapter"},
    )
    client.force_login(staff)

    response = client.post(
        "/admin-panel/providers/action/",
        {"action": "test", "kind": "payment", "provider_id": provider.id},
        follow=True,
    )

    content = response.content.decode("utf-8")
    assert "NOWPAYMENTS_API_KEY" in content
    assert AuditLog.objects.filter(action="provider.test").exists()


def test_test_action_reports_adapter_failure(client, staff):
    provider = CPAProvider.objects.create(
        code="base_net",
        name="Base Net",
        adapter_path="apps.cpa.providers.base.CPAProviderAdapter",
    )
    client.force_login(staff)

    response = client.post(
        "/admin-panel/providers/action/",
        {"action": "test", "kind": "cpa", "provider_id": provider.id},
        follow=True,
    )

    assert "test failed" in response.content.decode("utf-8")
