"""i18n tests: language switching, RTL rendering and Urdu translations."""
import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from django.utils import translation

from apps.wallets.services import get_wallet

pytestmark = pytest.mark.django_db

STRONG_PASSWORD = "StrongPass123!"


@pytest.fixture
def user():
    account = get_user_model().objects.create_user(
        email="i18n@example.com", password=STRONG_PASSWORD
    )
    get_wallet(account)
    return account


@pytest.fixture
def client():
    return Client()


def test_compiled_catalogue_is_usable():
    with translation.override("ur"):
        assert translation.gettext("Games") == "گیمز"
        assert translation.gettext("Wallet") == "والٹ"
        assert translation.gettext("Sponsored") == "اشتہار"


def test_default_language_is_ltr_english(client, user):
    client.force_login(user)

    response = client.get("/")

    assert response.status_code == 200
    assert b'lang="en"' in response.content
    assert b'dir="ltr"' in response.content
    assert b"Games" in response.content


def test_switch_to_urdu_renders_rtl_and_translations(client, user):
    client.force_login(user)

    response = client.post("/i18n/setlang/", {"language": "ur", "next": "/"})
    assert response.status_code == 302

    content = client.get("/").content.decode("utf-8")
    assert 'dir="rtl"' in content
    assert "گیمز" in content
    assert "والٹ" in content
