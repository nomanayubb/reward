"""Wallet API tests: balance summary and access control."""
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.rewards.models import Reward
from apps.rewards.services import RewardService
from apps.wallets.services import get_wallet

pytestmark = pytest.mark.django_db

SUMMARY_URL = "/api/v1/wallets/summary/"

STRONG_PASSWORD = "StrongPass123!"


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def user():
    account = get_user_model().objects.create_user(
        email="wallet@example.com", password=STRONG_PASSWORD
    )
    get_wallet(account)
    return account


def test_summary_requires_authentication(client):
    response = client.get(SUMMARY_URL)
    assert response.status_code in (401, 403)


def test_summary_shows_zero_balances_for_new_user(client, user):
    client.force_login(user)

    response = client.get(SUMMARY_URL)

    assert response.status_code == 200
    assert Decimal(response.data["cash"]) == Decimal("0")
    assert Decimal(response.data["pending"]) == Decimal("0")
    assert Decimal(response.data["points"]) == Decimal("0")
    assert response.data["currency"] == "PKR"


def test_summary_reflects_reward_balances(client, user):
    RewardService.award_fixed(
        user=user,
        source=Reward.Source.PROMOTION,
        cash=Decimal("7.25"),
        points=Decimal("150"),
        source_reference="wallet-summary-test",
    )
    client.force_login(user)

    response = client.get(SUMMARY_URL)

    assert response.status_code == 200
    assert Decimal(response.data["cash"]) == Decimal("7.25")
    assert Decimal(response.data["points"]) == Decimal("150.00")


def test_summary_isolates_users(client, user):
    other = get_user_model().objects.create_user(
        email="other@example.com", password=STRONG_PASSWORD
    )
    get_wallet(other)
    RewardService.award_fixed(
        user=other, source=Reward.Source.PROMOTION, cash=Decimal("99.00"), source_reference="other"
    )

    client.force_login(user)
    response = client.get(SUMMARY_URL)

    assert Decimal(response.data["cash"]) == Decimal("0")


def test_summary_includes_both_currencies(client, user):
    RewardService.award_fixed(
        user=user, source=Reward.Source.PROMOTION, cash=Decimal("100"), source_reference="pkr-side"
    )
    RewardService.award_fixed(
        user=user,
        source=Reward.Source.PROMOTION,
        cash=Decimal("5.00"),
        currency="USD",
        source_reference="usd-side",
    )

    client.force_login(user)
    response = client.get(SUMMARY_URL)

    assert response.data["currency"] == "PKR"
    assert Decimal(response.data["cash"]) == Decimal("100")

    balances = {bucket["currency"]: bucket for bucket in response.data["balances"]}
    assert Decimal(balances["PKR"]["cash"]) == Decimal("100")
    assert Decimal(balances["USD"]["cash"]) == Decimal("5.00")
