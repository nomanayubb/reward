"""Withdrawal API tests: request, list, methods."""
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.rewards.models import Reward
from apps.rewards.services import RewardService
from apps.wallets.services import get_wallet
from apps.withdrawals.models import Withdrawal, WithdrawalMethod
from apps.withdrawals.services import request_withdrawal

pytestmark = pytest.mark.django_db

WITHDRAWALS_URL = "/api/v1/withdrawals/"
METHODS_URL = "/api/v1/withdrawals/methods/"
SUMMARY_URL = "/api/v1/wallets/summary/"
STRONG_PASSWORD = "StrongPass123!"


@pytest.fixture
def user():
    account = get_user_model().objects.create_user(
        email="wd@example.com", password=STRONG_PASSWORD
    )
    get_wallet(account)
    RewardService.award_fixed(
        user=account,
        source=Reward.Source.PROMOTION,
        cash=Decimal("5000"),
        source_reference="wd-topup",
    )
    return account


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def method(user):
    return WithdrawalMethod.objects.create(
        user=user,
        type=WithdrawalMethod.Type.EASYPAISA,
        details={"account_number": "03001234567"},
    )


def test_withdrawals_require_authentication(client):
    assert client.get(WITHDRAWALS_URL).status_code in (401, 403)


def test_create_withdrawal_reserves_balance(client, user, method):
    client.force_login(user)
    response = client.post(
        WITHDRAWALS_URL, {"method": str(method.id), "amount": "1000.00"}, format="json"
    )

    assert response.status_code == 201
    assert response.data["status"] == Withdrawal.Status.REQUESTED
    assert Decimal(response.data["amount"]) == Decimal("1000.00")

    summary = client.get(SUMMARY_URL).data
    assert Decimal(summary["cash"]) == Decimal("4000.00")
    assert Decimal(summary["locked"]) == Decimal("1000.00")


def test_withdrawal_below_minimum_rejected(client, user, method):
    client.force_login(user)
    response = client.post(
        WITHDRAWALS_URL, {"method": str(method.id), "amount": "100.00"}, format="json"
    )

    assert response.status_code == 400
    assert "detail" in response.data


def test_withdrawal_list_is_user_scoped(client, user, method):
    other = get_user_model().objects.create_user(
        email="wd-other@example.com", password=STRONG_PASSWORD
    )
    get_wallet(other)
    other_method = WithdrawalMethod.objects.create(user=other, type=WithdrawalMethod.Type.JAZZCASH)
    RewardService.award_fixed(
        user=other,
        source=Reward.Source.PROMOTION,
        cash=Decimal("5000"),
        source_reference="other-topup",
    )
    request_withdrawal(user=other, method=other_method, amount=Decimal("1000"))

    client.force_login(user)
    client.post(WITHDRAWALS_URL, {"method": str(method.id), "amount": "1000.00"}, format="json")

    response = client.get(WITHDRAWALS_URL)

    assert response.status_code == 200
    assert response.data["count"] == 1
    assert response.data["results"][0]["method_type"] == "easypaisa"


def test_create_withdrawal_method(client, user):
    client.force_login(user)
    response = client.post(
        METHODS_URL,
        {
            "type": "easypaisa",
            "label": "My EasyPaisa",
            "details": {"account_number": "03001234567"},
        },
        format="json",
    )

    assert response.status_code == 201
    assert WithdrawalMethod.objects.filter(user=user).count() == 1


def test_cannot_use_another_users_method(client, user):
    other = get_user_model().objects.create_user(
        email="wd-other2@example.com", password=STRONG_PASSWORD
    )
    get_wallet(other)
    other_method = WithdrawalMethod.objects.create(user=other, type=WithdrawalMethod.Type.JAZZCASH)

    client.force_login(user)
    response = client.post(
        WITHDRAWALS_URL, {"method": str(other_method.id), "amount": "1000.00"}, format="json"
    )

    assert response.status_code == 400
