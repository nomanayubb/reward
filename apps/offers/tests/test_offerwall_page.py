"""AdGem Web Offerwall page tests."""
import pytest
from django.contrib.auth import get_user_model
from django.test import Client, override_settings

from apps.accounts.services import player_id_for
from apps.wallets.services import get_wallet

pytestmark = pytest.mark.django_db

OFFERWALL_URL = "/offers/offerwall/adgem/"


@pytest.fixture
def user():
    account = get_user_model().objects.create_user(
        email="wall@example.com", password="StrongPass123!"
    )
    get_wallet(account)
    return account


@pytest.fixture
def client():
    return Client()


def test_offerwall_requires_login(client):
    response = client.get(OFFERWALL_URL)
    assert response.status_code == 302


@override_settings(ADGEM_APP_ID="123")
def test_offerwall_embeds_wall_with_player_id(client, user):
    client.force_login(user)

    content = client.get(OFFERWALL_URL).content.decode("utf-8")

    assert "api.adgem.com/v1/wall?appid=123" in content
    assert f"playerid={player_id_for(user)}" in content


@override_settings(ADGEM_APP_ID="")
def test_offerwall_reports_missing_configuration(client, user):
    client.force_login(user)

    content = client.get(OFFERWALL_URL).content.decode("utf-8")

    assert "not configured" in content
    assert "api.adgem.com" not in content
