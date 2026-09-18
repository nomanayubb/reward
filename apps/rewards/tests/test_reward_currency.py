"""Reward currency behaviour (ADR-015 slice 2): PKR default + conversion."""
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model

from apps.rewards.models import Reward, RewardRule
from apps.rewards.services import RewardService
from apps.wallets.models import WalletAccount
from apps.wallets.services import get_account, get_wallet

pytestmark = pytest.mark.django_db

STRONG_PASSWORD = "StrongPass123!"


@pytest.fixture
def user():
    account = get_user_model().objects.create_user(
        email="pkr-reward@example.com", password=STRONG_PASSWORD
    )
    get_wallet(account)
    return account


def test_percentage_reward_is_converted_to_pkr(user):
    """Provider pays $2.00, rule 40% => $0.80 => PKR 224.00 at 280."""
    rule = RewardRule.objects.create(
        name="40% PKR", source=RewardRule.Source.OFFER, user_percentage=Decimal("40")
    )

    reward, _ = RewardService.award(
        user=user,
        source=Reward.Source.OFFER,
        source_reference="pkr-conversion",
        gross_revenue=Decimal("2.00"),
        rule=rule,
    )

    assert reward.currency == "PKR"
    assert reward.user_reward == Decimal("224.00000000")
    assert get_account(user, WalletAccount.Type.CASH, "PKR").balance == Decimal("224.00000000")
    assert get_account(user, WalletAccount.Type.CASH, "USD").balance == Decimal("0")


def test_exchange_rate_is_stored_on_the_reward(user):
    rule = RewardRule.objects.create(
        name="50% PKR", source=RewardRule.Source.OFFER, user_percentage=Decimal("50")
    )

    reward, _ = RewardService.award(
        user=user,
        source=Reward.Source.OFFER,
        source_reference="pkr-rate-stored",
        gross_revenue=Decimal("4.00"),
        rule=rule,
    )

    assert reward.metadata["exchange_rate"] == "280.00"
    assert reward.metadata["revenue_currency"] == "USD"
    assert reward.user_reward == Decimal("560.00000000")


def test_fixed_cash_is_already_in_reward_currency(user):
    rule = RewardRule.objects.create(
        name="Fixed PKR", source=RewardRule.Source.OFFER, fixed_cash=Decimal("50")
    )

    reward, _ = RewardService.award(
        user=user,
        source=Reward.Source.OFFER,
        source_reference="pkr-fixed",
        gross_revenue=Decimal("2.00"),
        rule=rule,
    )

    assert reward.currency == "PKR"
    assert reward.user_reward == Decimal("50.00000000")


def test_usd_rule_stays_in_usd(user):
    rule = RewardRule.objects.create(
        name="USD rule",
        source=RewardRule.Source.OFFER,
        user_percentage=Decimal("40"),
        reward_currency="USD",
    )

    reward, _ = RewardService.award(
        user=user,
        source=Reward.Source.OFFER,
        source_reference="usd-rule",
        gross_revenue=Decimal("2.00"),
        rule=rule,
    )

    assert reward.currency == "USD"
    assert reward.user_reward == Decimal("0.80")
    assert get_account(user, WalletAccount.Type.CASH, "USD").balance == Decimal("0.80")
    assert get_account(user, WalletAccount.Type.CASH, "PKR").balance == Decimal("0")


def test_award_fixed_defaults_to_pkr(user):
    reward, _ = RewardService.award_fixed(
        user=user, source=Reward.Source.PROMOTION, cash=Decimal("100"), source_reference="pkr-fixed"
    )

    assert reward.currency == "PKR"
    assert get_account(user, WalletAccount.Type.CASH, "PKR").balance == Decimal("100.00000000")
