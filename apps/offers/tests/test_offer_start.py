"""Offer click-through tests."""
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.test import Client

from apps.cpa.models import CPAProvider
from apps.offers.models import Offer, OfferClick
from apps.wallets.services import get_wallet

pytestmark = pytest.mark.django_db

STRONG_PASSWORD = "StrongPass123!"


@pytest.fixture
def user():
    account = get_user_model().objects.create_user(
        email="clicker@example.com", password=STRONG_PASSWORD
    )
    get_wallet(account)
    return account


@pytest.fixture
def client():
    return Client()


@pytest.fixture
def provider():
    return CPAProvider.objects.create(
        code="click_net",
        name="Click Net",
        adapter_path="apps.cpa.providers.base.CPAProviderAdapter",
        is_enabled=True,
    )


def _offer(provider, **overrides):
    defaults = {
        "provider": provider,
        "external_id": "click-1",
        "title": "Click offer",
        "payout": Decimal("2"),
        "user_reward": Decimal("560"),
        "incentive_allowed": True,
        "tracking_url": "https://provider.example/track",
    }
    defaults.update(overrides)
    return Offer.objects.create(**defaults)


def test_start_records_click_and_redirects(client, user, provider):
    offer = _offer(provider)
    client.force_login(user)

    response = client.get(f"/offers/{offer.id}/start/")

    assert response.status_code == 302
    assert response.url.startswith("https://provider.example/track")
    assert "subid=" in response.url

    click = OfferClick.objects.get(user=user, offer=offer)
    assert click.click_id in response.url


def test_start_blocks_ineligible_offer(client, user, provider):
    offer = _offer(provider, incentive_allowed=False)
    client.force_login(user)

    response = client.get(f"/offers/{offer.id}/start/")

    assert response.status_code == 302
    assert response.url == "/offers/"
    assert OfferClick.objects.count() == 0


def test_start_without_tracking_url_reports_error(client, user, provider):
    offer = _offer(provider, tracking_url="")
    client.force_login(user)

    response = client.get(f"/offers/{offer.id}/start/")

    assert response.url == "/offers/"
    assert OfferClick.objects.count() == 1
