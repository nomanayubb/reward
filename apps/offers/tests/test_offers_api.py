"""Offer catalog API tests: only eligible offers are listed."""
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.cpa.models import CPAProvider
from apps.offers.models import Offer
from apps.wallets.services import get_wallet

pytestmark = pytest.mark.django_db

OFFERS_URL = "/api/v1/offers/"
STRONG_PASSWORD = "StrongPass123!"


@pytest.fixture
def user():
    account = get_user_model().objects.create_user(
        email="offers@example.com", password=STRONG_PASSWORD
    )
    get_wallet(account)
    return account


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def provider():
    return CPAProvider.objects.create(
        code="network_a",
        name="Network A",
        adapter_path="apps.cpa.providers.base.CPAProviderAdapter",
        is_enabled=True,
    )


def _offer(provider, external_id, **overrides):
    defaults = {
        "provider": provider,
        "external_id": external_id,
        "title": f"Offer {external_id}",
        "payout": Decimal("2.00"),
        "user_reward": Decimal("224.00"),
        "incentive_allowed": True,
    }
    defaults.update(overrides)
    return Offer.objects.create(**defaults)


def test_offers_list_requires_authentication(client):
    assert client.get(OFFERS_URL).status_code in (401, 403)


def test_offers_list_returns_eligible_offers_only(client, user, provider):
    eligible = _offer(provider, "ok")
    _offer(provider, "no-incentive", incentive_allowed=False)
    _offer(provider, "paused", status=Offer.Status.PAUSED)

    client.force_login(user)
    response = client.get(OFFERS_URL)

    assert response.status_code == 200
    ids = [row["id"] for row in response.data["results"]]
    assert ids == [str(eligible.id)]


def test_offer_payload_hides_tracking_url(client, user, provider):
    _offer(provider, "tracking", tracking_url="https://provider.example/track?sub=")

    client.force_login(user)
    row = client.get(OFFERS_URL).data["results"][0]

    assert "tracking_url" not in row
    assert row["user_reward"] == "224.00000000"
    assert row["provider"] == "Network A"
