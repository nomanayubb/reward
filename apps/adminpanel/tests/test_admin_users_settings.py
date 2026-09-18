"""Admin user management and configuration center tests."""
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.test import Client

from apps.adminpanel.models import AuditLog, ConfigurationVersion, FeatureFlag, PlatformSetting
from apps.users.models import UserRestriction
from apps.wallets.models import WalletAccount
from apps.wallets.services import get_account, get_wallet

pytestmark = pytest.mark.django_db

STRONG_PASSWORD = "StrongPass123!"


@pytest.fixture
def staff():
    account = get_user_model().objects.create_user(
        email="staff2@example.com", password=STRONG_PASSWORD, is_staff=True
    )
    get_wallet(account)
    return account


@pytest.fixture
def player():
    account = get_user_model().objects.create_user(
        email="target@example.com", password=STRONG_PASSWORD
    )
    get_wallet(account)
    return account


@pytest.fixture
def client():
    return Client()


def test_user_pages_require_staff(client, player):
    client.force_login(player)

    assert client.get("/admin-panel/users/").status_code == 403
    assert client.get(f"/admin-panel/users/{player.id}/").status_code == 403


def test_user_search(client, staff, player):
    client.force_login(staff)

    response = client.get("/admin-panel/users/", {"q": "target@"})
    assert response.status_code == 200
    assert b"target@example.com" in response.content

    response = client.get("/admin-panel/users/", {"q": "nobody@"})
    assert b"target@example.com" not in response.content


def test_freeze_and_unfreeze(client, staff, player):
    client.force_login(staff)

    client.post(f"/admin-panel/users/{player.id}/action/", {"action": "freeze"})
    player.refresh_from_db()
    assert player.status == player.Status.FROZEN

    client.post(f"/admin-panel/users/{player.id}/action/", {"action": "unfreeze"})
    player.refresh_from_db()
    assert player.status == player.Status.ACTIVE


def test_restriction_and_removal(client, staff, player):
    client.force_login(staff)

    client.post(
        f"/admin-panel/users/{player.id}/action/",
        {"action": "restrict", "type": "withdrawal_disabled", "reason": "review"},
    )
    restriction = UserRestriction.objects.get(user=player, type="withdrawal_disabled")
    assert restriction.is_active is True

    client.post(
        f"/admin-panel/users/{player.id}/action/",
        {"action": "unrestrict", "restriction_id": restriction.id},
    )
    restriction.refresh_from_db()
    assert restriction.is_active is False


def test_balance_adjustment_credits_and_audits(client, staff, player):
    client.force_login(staff)

    client.post(
        f"/admin-panel/users/{player.id}/action/",
        {"action": "adjust", "amount": "1500", "currency": "PKR", "reason": "goodwill"},
    )

    assert get_account(player, WalletAccount.Type.CASH, "PKR").balance == Decimal(
        "1500.00000000"
    )
    assert AuditLog.objects.filter(action="wallet.adjust", object_id=str(player.id)).exists()


def test_settings_update_creates_version(client, staff):
    client.force_login(staff)

    client.post("/admin-panel/settings/", {"key": "MIN_WITHDRAWAL_PKR", "value": "750"})

    setting = PlatformSetting.objects.get(key="MIN_WITHDRAWAL_PKR")
    assert setting.value == 750
    assert ConfigurationVersion.objects.filter(key="MIN_WITHDRAWAL_PKR").exists()
    assert AuditLog.objects.filter(action="settings.update").exists()


def test_feature_flag_toggle(client, staff):
    flag = FeatureFlag.objects.create(key="FEATURE_TEST", is_enabled=False)
    client.force_login(staff)

    client.post("/admin-panel/flags/", {"flag_id": flag.id})

    flag.refresh_from_db()
    assert flag.is_enabled is True
