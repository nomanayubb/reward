"""Withdrawal limits are configured in PKR (ADR-015 slice 3)."""
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model

from apps.adminpanel.settings import set_setting
from apps.kyc.models import KYCVerification
from apps.rewards.models import Reward
from apps.rewards.services import RewardService
from apps.wallets.services import get_wallet
from apps.withdrawals.models import WithdrawalMethod
from apps.withdrawals.services import WithdrawalError, request_withdrawal

pytestmark = pytest.mark.django_db

STRONG_PASSWORD = "StrongPass123!"


@pytest.fixture
def user():
    account = get_user_model().objects.create_user(
        email="limits@example.com", password=STRONG_PASSWORD
    )
    get_wallet(account)
    RewardService.award_fixed(
        user=account,
        source=Reward.Source.PROMOTION,
        cash=Decimal("200000"),
        source_reference="limits-topup",
    )
    return account


@pytest.fixture
def method(user):
    return WithdrawalMethod.objects.create(user=user, type=WithdrawalMethod.Type.EASYPAISA)


def test_below_minimum_rejected(user, method):
    with pytest.raises(WithdrawalError):
        request_withdrawal(user=user, method=method, amount=Decimal("100.00"))


def test_above_maximum_rejected(user, method):
    with pytest.raises(WithdrawalError):
        request_withdrawal(user=user, method=method, amount=Decimal("150000.00"))


def test_kyc_required_at_threshold(user, method):
    with pytest.raises(WithdrawalError):
        request_withdrawal(user=user, method=method, amount=Decimal("6000.00"))

    KYCVerification.objects.create(user=user, status=KYCVerification.Status.APPROVED)

    withdrawal = request_withdrawal(user=user, method=method, amount=Decimal("6000.00"))
    assert withdrawal.amount == Decimal("6000.00000000")


def test_usd_limits_are_converted_from_pkr(user, method):
    """PKR min 500 => USD min 500/280 ≈ 1.79, so a $1.00 request is rejected."""
    RewardService.award_fixed(
        user=user,
        source=Reward.Source.PROMOTION,
        cash=Decimal("50.00"),
        currency="USD",
        source_reference="usd-topup",
    )

    with pytest.raises(WithdrawalError):
        request_withdrawal(user=user, method=method, amount=Decimal("1.00"), currency="USD")

    withdrawal = request_withdrawal(user=user, method=method, amount=Decimal("2.00"), currency="USD")
    assert withdrawal.currency == "USD"


def test_custom_admin_minimum_is_respected(user, method):
    set_setting("MIN_WITHDRAWAL_PKR", "2000.00", group="withdrawals")

    with pytest.raises(WithdrawalError):
        request_withdrawal(user=user, method=method, amount=Decimal("1500.00"))

    withdrawal = request_withdrawal(user=user, method=method, amount=Decimal("2000.00"))
    assert withdrawal.amount == Decimal("2000.00000000")
