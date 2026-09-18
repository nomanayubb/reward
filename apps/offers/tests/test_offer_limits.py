"""Offer remaining-limit tests."""
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.test import Client

from apps.cpa.models import CPAProvider
from apps.offers.models import Offer, OfferConversion
from apps.offers.services import limit_status
from apps.wallets.services import get_wallet

pytestmark = pytest.mark.django_db

STRONG_PASSWORD = "StrongPass123!"


@pytest.fixture
def user():
    account = get_user_model().objects.create_user(
        email="limits-offer@example.com", password=STRONG_PASSWORD
    )
    get_wallet(account)
    return account


@pytest.fixture
def client():
    return Client()


@pytest.fixture
def provider():
    return CPAProvider.objects.create(
        code="limits_net",
        name="Limits Net",
        adapter_path="apps.cpa.providers.base.CPAProviderAdapter",
        is_enabled=True,
    )


@pytest.fixture
def offer(provider):
    return Offer.objects.create(
        provider=provider,
        external_id="limits-1",
        title="Limited offer",
        payout=Decimal("2"),
        user_reward=Decimal("560"),
        incentive_allowed=True,
        daily_user_limit=2,
        lifetime_user_limit=3,
    )


def _convert(user, offer, ref):
    return OfferConversion.objects.create(
        user=user,
        offer=offer,
        provider=offer.provider,
        external_conversion_id=ref,
        payout=Decimal("2"),
        user_reward=Decimal("560"),
        status=OfferConversion.Status.APPROVED,
    )


def test_limit_status_counts_remaining(user, offer):
    status = limit_status(user, offer)

    assert status["daily_remaining"] == 2
    assert status["lifetime_remaining"] == 3
    assert status["can_complete"] is True


def test_limit_status_after_conversion(user, offer):
    _convert(user, offer, "c1")

    status = limit_status(user, offer)

    assert status["daily_remaining"] == 1
    assert status["lifetime_remaining"] == 2


def test_lifetime_exhausted_blocks_completion(user, offer):
    for index in range(3):
        _convert(user, offer, f"c{index}")

    status = limit_status(user, offer)

    assert status["lifetime_remaining"] == 0
    assert status["can_complete"] is False


def test_offers_page_shows_remaining_and_unavailable(client, user, offer):
    for index in range(3):
        _convert(user, offer, f"page-{index}")

    client.force_login(user)
    content = client.get("/offers/").content.decode("utf-8")

    assert "Not available right now" in content
    assert "Limited offer" in content
    assert "used all your completions" in content
