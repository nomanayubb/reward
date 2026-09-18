"""Notification API tests."""
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.notifications.models import Notification
from apps.wallets.services import get_wallet

pytestmark = pytest.mark.django_db

NOTIFICATIONS_URL = "/api/v1/notifications/"
UNREAD_COUNT_URL = "/api/v1/notifications/unread-count/"
READ_ALL_URL = "/api/v1/notifications/read-all/"
STRONG_PASSWORD = "StrongPass123!"


@pytest.fixture
def user():
    account = get_user_model().objects.create_user(
        email="notify@example.com", password=STRONG_PASSWORD
    )
    get_wallet(account)
    return account


@pytest.fixture
def client():
    return APIClient()


def test_notifications_require_authentication(client):
    assert client.get(NOTIFICATIONS_URL).status_code in (401, 403)


def test_list_returns_own_notifications(client, user):
    other = get_user_model().objects.create_user(
        email="notify-other@example.com", password=STRONG_PASSWORD
    )
    Notification.objects.create(user=user, title="Welcome")
    Notification.objects.create(user=other, title="Theirs")

    client.force_login(user)
    response = client.get(NOTIFICATIONS_URL)

    assert response.status_code == 200
    assert response.data["count"] == 1
    assert response.data["results"][0]["title"] == "Welcome"


def test_unread_filter_and_count(client, user):
    Notification.objects.create(user=user, title="Unread one")
    Notification.objects.create(user=user, title="Read one", is_read=True)

    client.force_login(user)

    assert client.get(NOTIFICATIONS_URL, {"unread": "1"}).data["count"] == 1
    assert client.get(UNREAD_COUNT_URL).data["unread"] == 1


def test_mark_read_and_read_all(client, user):
    first = Notification.objects.create(user=user, title="A")
    Notification.objects.create(user=user, title="B")

    client.force_login(user)
    assert client.post(f"{NOTIFICATIONS_URL}{first.id}/read/").status_code == 200

    first.refresh_from_db()
    assert first.is_read is True

    response = client.post(READ_ALL_URL)
    assert response.data["marked_read"] == 1
    assert Notification.objects.filter(user=user, is_read=False).count() == 0


def test_cannot_mark_another_users_notification(client, user):
    other = get_user_model().objects.create_user(
        email="notify-other2@example.com", password=STRONG_PASSWORD
    )
    theirs = Notification.objects.create(user=other, title="Theirs")

    client.force_login(user)
    response = client.post(f"{NOTIFICATIONS_URL}{theirs.id}/read/")

    assert response.status_code == 404
