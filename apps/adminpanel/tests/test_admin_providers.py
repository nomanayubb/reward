"""Provider management and emergency kill-switch tests."""
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.adminpanel.models import AuditLog
from apps.adminpanel.settings import set_setting
from apps.cpa.models import CPAProvider
from apps.deposits.services import DepositError, create_deposit
from apps.games.models import Game
from apps.games.services import start_session
from apps.payments.models import PaymentProvider
from apps.wallets.services import get_wallet

pytestmark = pytest.mark.django_db

STRONG_PASSWORD = "StrongPass123!"


@pytest.fixture
def staff():
    account = get_user_model().objects.create_user(
        email="staff3@example.com", password=STRONG_PASSWORD, is_staff=True
    )
    get_wallet(account)
    return account


@pytest.fixture
def player():
    account = get_user_model().objects.create_user(
        email="switch-player@example.com", password=STRONG_PASSWORD
    )
    get_wallet(account)
    return account


@pytest.fixture
def client():
    return APIClient()


def test_providers_page_requires_staff(client, player):
    client.force_login(player)
    assert client.get("/admin-panel/providers/").status_code == 403


def test_providers_page_renders_switches(client, staff):
    client.force_login(staff)

    response = client.get("/admin-panel/providers/")

    assert response.status_code == 200
    assert b"Emergency switches" in response.content


def test_toggle_provider(client, staff):
    provider = CPAProvider.objects.create(
        code="kill_switch_net",
        name="Kill Switch Net",
        adapter_path="apps.cpa.providers.base.CPAProviderAdapter",
        is_enabled=True,
    )
    client.force_login(staff)

    client.post(
        "/admin-panel/providers/action/",
        {"action": "toggle_provider", "kind": "cpa", "provider_id": provider.id},
    )

    provider.refresh_from_db()
    assert provider.is_enabled is False
    assert AuditLog.objects.filter(action="provider.toggle").exists()


def test_emergency_switch_blocks_deposits(client, staff, player):
    provider = PaymentProvider.objects.create(
        code="manual2",
        name="Manual",
        kind=PaymentProvider.Kind.LOCAL,
        is_enabled=True,
        supports_deposits=True,
        config={"adapter_path": "apps.payments.providers.manual.ManualProviderAdapter"},
    )
    client.force_login(staff)

    client.post(
        "/admin-panel/providers/action/",
        {"action": "switch", "key": "DEPOSITS_ENABLED", "value": "off"},
    )

    with pytest.raises(DepositError):
        create_deposit(user=player, provider=provider, amount=Decimal("1000"))
    assert AuditLog.objects.filter(action="switch.toggle").exists()


def test_emergency_switch_blocks_games(client, staff, player):
    game = Game.objects.create(slug="switch-game", title="Switch Game", entry_path="game.html")
    set_setting("GAMES_ENABLED", False, group="switches")

    with pytest.raises(ValueError):
        start_session(player, game)


def test_emergency_switch_blocks_offers(client, staff, player):
    set_setting("OFFERS_ENABLED", False, group="switches")
    client.force_login(player)

    response = client.get("/api/v1/offers/")

    assert response.status_code == 200
    assert response.data["count"] == 0


def test_emergency_switch_blocks_surveys(client, staff, player):
    set_setting("SURVEYS_ENABLED", False, group="switches")
    client.force_login(player)

    response = client.get("/api/v1/surveys/")

    assert response.status_code == 200
    assert response.data["count"] == 0
