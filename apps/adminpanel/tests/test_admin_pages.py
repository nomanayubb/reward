"""Admin panel page tests: access control, dashboard metrics, withdrawal queue."""
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.test import Client

from apps.adminpanel.models import AuditLog
from apps.rewards.models import Reward
from apps.rewards.services import RewardService
from apps.wallets.models import WalletAccount
from apps.wallets.services import get_account, get_wallet
from apps.withdrawals.models import Withdrawal, WithdrawalMethod
from apps.withdrawals.services import request_withdrawal

pytestmark = pytest.mark.django_db

STRONG_PASSWORD = "StrongPass123!"


@pytest.fixture
def staff():
    account = get_user_model().objects.create_user(
        email="staff@example.com", password=STRONG_PASSWORD, is_staff=True
    )
    get_wallet(account)
    return account


@pytest.fixture
def player():
    account = get_user_model().objects.create_user(
        email="player-admin@example.com", password=STRONG_PASSWORD
    )
    get_wallet(account)
    RewardService.award_fixed(
        user=account,
        source=Reward.Source.PROMOTION,
        cash=Decimal("5000"),
        source_reference="admin-test-topup",
    )
    return account


@pytest.fixture
def client():
    return Client()


def _make_withdrawal(player):
    method = WithdrawalMethod.objects.create(
        user=player,
        type=WithdrawalMethod.Type.EASYPAISA,
        details={"account_number": "03001234567"},
    )
    return request_withdrawal(user=player, method=method, amount=Decimal("1000"))


def test_admin_pages_require_login(client):
    assert client.get("/admin-panel/").status_code == 302


def test_admin_pages_require_staff(client, player):
    client.force_login(player)
    assert client.get("/admin-panel/").status_code == 403


def test_dashboard_renders_metrics(client, staff, player):
    client.force_login(staff)

    response = client.get("/admin-panel/")

    assert response.status_code == 200
    assert b"Operations dashboard" in response.content
    assert b"User liability PKR" in response.content


def test_withdrawal_queue_lists_requests(client, staff, player):
    _make_withdrawal(player)
    client.force_login(staff)

    response = client.get("/admin-panel/withdrawals/")

    assert response.status_code == 200
    assert b"player-admin@example.com" in response.content


def test_withdrawal_full_lifecycle(client, staff, player):
    withdrawal = _make_withdrawal(player)
    client.force_login(staff)

    response = client.post(
        f"/admin-panel/withdrawals/{withdrawal.id}/action/", {"action": "approve"}
    )
    assert response.status_code == 302
    withdrawal.refresh_from_db()
    assert withdrawal.status == Withdrawal.Status.PROCESSING

    client.post(
        f"/admin-panel/withdrawals/{withdrawal.id}/action/",
        {"action": "pay", "reference": "EASY-123"},
    )
    withdrawal.refresh_from_db()
    assert withdrawal.status == Withdrawal.Status.PAID
    assert withdrawal.payment_reference == "EASY-123"


def test_reject_refunds_the_user(client, staff, player):
    withdrawal = _make_withdrawal(player)
    client.force_login(staff)

    client.post(
        f"/admin-panel/withdrawals/{withdrawal.id}/action/",
        {"action": "reject", "reason": "test rejection"},
    )
    withdrawal.refresh_from_db()

    assert withdrawal.status == Withdrawal.Status.REJECTED
    assert get_account(player, WalletAccount.Type.CASH).balance == Decimal("5000.00000000")


def test_actions_are_audited(client, staff, player):
    withdrawal = _make_withdrawal(player)
    client.force_login(staff)

    client.post(f"/admin-panel/withdrawals/{withdrawal.id}/action/", {"action": "approve"})

    assert AuditLog.objects.filter(
        action="withdrawal.approve", object_id=str(withdrawal.id)
    ).exists()
