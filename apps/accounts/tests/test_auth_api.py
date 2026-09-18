"""Auth API tests: registration, login, session identity, logout, referrals."""
import pytest
from django.contrib.auth import get_user_model
from django.core.cache import cache
from rest_framework.test import APIClient

from apps.referrals.models import Referral
from apps.wallets.models import WalletAccount

pytestmark = pytest.mark.django_db

REGISTER_URL = "/api/v1/auth/register/"
LOGIN_URL = "/api/v1/auth/login/"
LOGOUT_URL = "/api/v1/auth/logout/"
ME_URL = "/api/v1/auth/me/"

STRONG_PASSWORD = "StrongPass123!"


@pytest.fixture(autouse=True)
def _clear_throttle_cache():
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def client():
    return APIClient()


def test_register_creates_user_and_wallet(client):
    response = client.post(
        REGISTER_URL,
        {"email": "New.User@Example.com", "password": STRONG_PASSWORD},
        format="json",
    )

    assert response.status_code == 201
    user = get_user_model().objects.get(email="new.user@example.com")
    assert user.check_password(STRONG_PASSWORD)
    assert user.wallet.accounts.filter(type=WalletAccount.Type.CASH).exists()
    assert response.data["email"] == "new.user@example.com"
    assert response.data["referral_code"]


def test_register_duplicate_email_rejected(client):
    get_user_model().objects.create_user(email="taken@example.com", password=STRONG_PASSWORD)

    response = client.post(
        REGISTER_URL, {"email": "taken@example.com", "password": STRONG_PASSWORD}, format="json"
    )

    assert response.status_code == 400
    assert "email" in response.data


def test_register_weak_password_rejected(client):
    response = client.post(
        REGISTER_URL, {"email": "weak@example.com", "password": "12345678"}, format="json"
    )

    assert response.status_code == 400
    assert "password" in response.data


def test_register_with_referral_code_creates_referral(client):
    referrer = get_user_model().objects.create_user(
        email="referrer@example.com", password=STRONG_PASSWORD
    )

    response = client.post(
        REGISTER_URL,
        {
            "email": "referred@example.com",
            "password": STRONG_PASSWORD,
            "referral_code": referrer.referral_code,
        },
        format="json",
    )

    assert response.status_code == 201
    referred = get_user_model().objects.get(email="referred@example.com")
    referral = Referral.objects.get(referred=referred)
    assert referral.referrer == referrer


def test_login_and_me(client):
    user = get_user_model().objects.create_user(
        email="player@example.com", password=STRONG_PASSWORD
    )

    login_response = client.post(
        LOGIN_URL, {"email": "player@example.com", "password": STRONG_PASSWORD}, format="json"
    )
    assert login_response.status_code == 200

    me_response = client.get(ME_URL)
    assert me_response.status_code == 200
    assert me_response.data["id"] == str(user.id)


def test_login_wrong_password_rejected(client):
    get_user_model().objects.create_user(email="player2@example.com", password=STRONG_PASSWORD)

    response = client.post(
        LOGIN_URL, {"email": "player2@example.com", "password": "wrong-password"}, format="json"
    )

    assert response.status_code == 400


def test_me_requires_authentication(client):
    response = client.get(ME_URL)
    assert response.status_code in (401, 403)


def test_logout_ends_session(client):
    get_user_model().objects.create_user(email="bye@example.com", password=STRONG_PASSWORD)
    client.post(
        LOGIN_URL, {"email": "bye@example.com", "password": STRONG_PASSWORD}, format="json"
    )

    logout_response = client.post(LOGOUT_URL)
    assert logout_response.status_code == 204

    me_response = client.get(ME_URL)
    assert me_response.status_code in (401, 403)
