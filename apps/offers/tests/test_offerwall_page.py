"""Generic offerwall hub tests: any network, driven by its adapter template."""
import pytest
from django.contrib.auth import get_user_model
from django.test import Client, override_settings

from apps.accounts.services import player_id_for
from apps.cpa.models import CPAProvider
from apps.cpa.providers.base import CPAProviderAdapter
from apps.wallets.services import get_wallet

pytestmark = pytest.mark.django_db

INDEX_URL = "/offers/offerwall/"
ADGEM_URL = "/offers/offerwall/adgem/"


class NoWallAdapter(CPAProviderAdapter):
    """Adapter without a pre-built offerwall (template left empty)."""

    code = "nowall"


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


@pytest.fixture
def provider():
    return CPAProvider.objects.create(
        code="adgem",
        name="AdGem",
        adapter_path="apps.cpa.providers.adgem.AdgemAdapter",
        is_enabled=True,
        config={},
    )


def test_index_requires_login(client):
    assert client.get(INDEX_URL).status_code == 302


def test_provider_page_requires_login(client, provider):
    assert client.get(ADGEM_URL).status_code == 302


@override_settings(ADGEM_APP_ID="123")
def test_provider_page_embeds_wall_with_player_id(client, user, provider):
    client.force_login(user)

    content = client.get(ADGEM_URL).content.decode("utf-8")

    assert "api.adgem.com/v1/wall?appid=123" in content
    assert f"playerid={player_id_for(user)}" in content


@override_settings(ADGEM_APP_ID="")
def test_provider_page_404_without_app_id(client, user, provider):
    client.force_login(user)

    assert client.get(ADGEM_URL).status_code == 404


def test_provider_config_overrides_template(client, user, provider):
    provider.config = {"offerwall_url_template": "https://wall.example.com?uid={player_id}"}
    provider.save(update_fields=["config"])
    client.force_login(user)

    content = client.get(ADGEM_URL).content.decode("utf-8")

    assert "https://wall.example.com?uid=" in content
    assert "api.adgem.com" not in content


def test_provider_page_404_when_disabled(client, user, provider):
    provider.is_enabled = False
    provider.save(update_fields=["is_enabled"])
    client.force_login(user)

    assert client.get(ADGEM_URL).status_code == 404


def test_provider_page_404_when_no_template(client, user):
    CPAProvider.objects.create(
        code="nowall",
        name="No Wall",
        adapter_path="apps.offers.tests.test_offerwall_page.NoWallAdapter",
        is_enabled=True,
        config={},
    )
    client.force_login(user)

    assert client.get("/offers/offerwall/nowall/").status_code == 404


@override_settings(ADGEM_APP_ID="123")
def test_index_lists_only_networks_with_offerwalls(client, user, provider):
    CPAProvider.objects.create(
        code="nowall",
        name="No Wall",
        adapter_path="apps.offers.tests.test_offerwall_page.NoWallAdapter",
        is_enabled=True,
        config={},
    )
    CPAProvider.objects.create(
        code="zzz",
        name="ZzzDisabled",
        adapter_path="apps.cpa.providers.adgem.AdgemAdapter",
        is_enabled=False,
        config={},
    )
    client.force_login(user)

    content = client.get(INDEX_URL).content.decode("utf-8")

    assert "AdGem" in content
    assert "No Wall" not in content
    assert "ZzzDisabled" not in content
