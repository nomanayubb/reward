"""Report generation tests."""
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.test import Client

from apps.reports.models import ReportJob
from apps.rewards.models import Reward
from apps.rewards.services import RewardService
from apps.wallets.services import get_wallet

pytestmark = pytest.mark.django_db

STRONG_PASSWORD = "StrongPass123!"


@pytest.fixture
def staff():
    account = get_user_model().objects.create_user(
        email="staff-report@example.com", password=STRONG_PASSWORD, is_staff=True
    )
    get_wallet(account)
    return account


@pytest.fixture
def player():
    account = get_user_model().objects.create_user(
        email="player-report@example.com", password=STRONG_PASSWORD
    )
    get_wallet(account)
    RewardService.award_fixed(
        user=account,
        source=Reward.Source.PROMOTION,
        cash=Decimal("500"),
        source_reference="report-topup",
    )
    return account


@pytest.fixture
def client():
    return Client()


def test_reports_page_requires_staff(client, player):
    client.force_login(player)
    assert client.get("/admin-panel/reports/").status_code == 403


def test_generate_financial_report(client, staff, player, settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path
    client.force_login(staff)

    response = client.post("/admin-panel/reports/", {"kind": "financial"})

    assert response.status_code == 302
    job = ReportJob.objects.latest("created_at")
    assert job.status == ReportJob.Status.READY

    content = job.file.read().decode("utf-8")
    assert "user_reward" in content
    assert "player-report@example.com" in content


def test_generate_users_report(client, staff, settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path
    client.force_login(staff)

    client.post("/admin-panel/reports/", {"kind": "users"})

    job = ReportJob.objects.latest("created_at")
    content = job.file.read().decode("utf-8")
    assert "email" in content
    assert "staff-report@example.com" in content


def test_unknown_kind_rejected(client, staff):
    client.force_login(staff)

    client.post("/admin-panel/reports/", {"kind": "bogus"})

    assert ReportJob.objects.count() == 0
