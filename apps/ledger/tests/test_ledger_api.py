"""Ledger API tests: user-scoped transaction history and filters."""
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.rewards.models import Reward
from apps.rewards.services import RewardService
from apps.wallets.services import get_wallet

pytestmark = pytest.mark.django_db

TRANSACTIONS_URL = "/api/v1/ledger/transactions/"

STRONG_PASSWORD = "StrongPass123!"


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def user():
    account = get_user_model().objects.create_user(
        email="ledger@example.com", password=STRONG_PASSWORD
    )
    get_wallet(account)
    return account


def test_transactions_require_authentication(client):
    response = client.get(TRANSACTIONS_URL)
    assert response.status_code in (401, 403)


def test_transactions_are_scoped_to_the_user(client, user):
    other = get_user_model().objects.create_user(
        email="other-ledger@example.com", password=STRONG_PASSWORD
    )
    get_wallet(other)

    RewardService.award_fixed(
        user=user, source=Reward.Source.PROMOTION, cash=Decimal("3.00"), source_reference="mine"
    )
    RewardService.award_fixed(
        user=other, source=Reward.Source.PROMOTION, cash=Decimal("99.00"), source_reference="theirs"
    )

    client.force_login(user)
    response = client.get(TRANSACTIONS_URL)

    assert response.status_code == 200
    amounts = {Decimal(row["amount"]) for row in response.data["results"]}
    assert Decimal("3.00") in amounts
    assert Decimal("99.00") not in amounts
    # One reward produces three user-side entries: pending credit, then the
    # approval pair (pending debit + cash credit).
    assert response.data["count"] == 3


def test_transactions_type_filter(client, user):
    RewardService.award_fixed(
        user=user, source=Reward.Source.PROMOTION, cash=Decimal("4.00"), source_reference="filter-me"
    )
    client.force_login(user)

    reward_rows = client.get(TRANSACTIONS_URL, {"type": "reward"}).data
    deposit_rows = client.get(TRANSACTIONS_URL, {"type": "deposit"}).data

    assert reward_rows["count"] == 3
    assert deposit_rows["count"] == 0


def test_transaction_rows_include_transaction_metadata(client, user):
    RewardService.award_fixed(
        user=user, source=Reward.Source.PROMOTION, cash=Decimal("5.00"), source_reference="meta"
    )
    client.force_login(user)

    row = client.get(TRANSACTIONS_URL).data["results"][0]

    assert row["type"] == "reward"
    assert row["status"] == "posted"
    assert row["account_type"] == "cash"
    assert row["transaction_id"]
    assert row["created_at"]
