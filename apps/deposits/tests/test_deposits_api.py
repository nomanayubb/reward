"""Deposit API tests using the manual provider adapter."""
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.deposits.models import Deposit
from apps.deposits.services import create_deposit
from apps.payments.models import PaymentProvider, PaymentTransaction
from apps.wallets.services import get_wallet

pytestmark = pytest.mark.django_db

DEPOSITS_URL = "/api/v1/deposits/"
STRONG_PASSWORD = "StrongPass123!"


@pytest.fixture
def user():
    account = get_user_model().objects.create_user(
        email="dep@example.com", password=STRONG_PASSWORD
    )
    get_wallet(account)
    return account


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def provider():
    return PaymentProvider.objects.create(
        code="manual",
        name="Manual",
        kind=PaymentProvider.Kind.LOCAL,
        is_enabled=True,
        supports_deposits=True,
        config={"adapter_path": "apps.payments.providers.manual.ManualProviderAdapter"},
    )


def test_deposits_require_authentication(client):
    assert client.get(DEPOSITS_URL).status_code in (401, 403)


def test_create_deposit_returns_instructions(client, user, provider):
    client.force_login(user)
    response = client.post(
        DEPOSITS_URL, {"provider": "manual", "amount": "1000.00"}, format="json"
    )

    assert response.status_code == 201
    assert response.data["status"] == Deposit.Status.AWAITING_PAYMENT
    assert response.data["currency"] == "PKR"
    assert response.data["payment_instructions"]["reference"]
    assert (
        PaymentTransaction.objects.filter(
            user=user, direction=PaymentTransaction.Direction.DEPOSIT
        ).count()
        == 1
    )


def test_disabled_provider_rejected(client, user, provider):
    provider.is_enabled = False
    provider.save(update_fields=["is_enabled"])

    client.force_login(user)
    response = client.post(
        DEPOSITS_URL, {"provider": "manual", "amount": "1000.00"}, format="json"
    )

    assert response.status_code == 400


def test_deposit_list_is_user_scoped(client, user, provider):
    other = get_user_model().objects.create_user(
        email="dep-other@example.com", password=STRONG_PASSWORD
    )
    get_wallet(other)
    create_deposit(user=other, provider=provider, amount=Decimal("500"))

    client.force_login(user)
    client.post(DEPOSITS_URL, {"provider": "manual", "amount": "1000.00"}, format="json")

    response = client.get(DEPOSITS_URL)

    assert response.status_code == 200
    assert response.data["count"] == 1
    assert Decimal(response.data["results"][0]["amount"]) == Decimal("1000.00")
