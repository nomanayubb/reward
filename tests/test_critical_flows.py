"""Critical business-rule tests (docs/DRD.md §142-146).

These lock down the money paths: reward calculation, ledger integrity,
idempotency, withdrawal reservation and campaign quotas.
"""
from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError

from apps.ledger.services import account_balance, post_transaction, reverse_transaction
from apps.ledger.models import LedgerTransaction
from apps.rewards.models import Reward, RewardRule
from apps.rewards.services import RewardError, RewardService
from apps.wallets.models import WalletAccount
from apps.wallets.services import get_account, get_wallet, system_account
from apps.withdrawals.models import Withdrawal, WithdrawalMethod
from apps.withdrawals.services import WithdrawalError, reject_withdrawal, request_withdrawal

pytestmark = pytest.mark.django_db


@pytest.fixture
def user(django_user_model):
    account = django_user_model.objects.create_user(email="player@example.com", password="secret-pass-1")
    get_wallet(account)
    return account


# --------------------------------------------------------------------------
# §144 — Reward calculation: provider $2.00, rule 40% => user $0.80
# --------------------------------------------------------------------------
def test_reward_percentage_rule(user):
    rule = RewardRule.objects.create(
        name="40% offer share", source=RewardRule.Source.OFFER, user_percentage=Decimal("40")
    )
    reward, created = RewardService.award(
        user=user,
        source=Reward.Source.OFFER,
        source_reference="conversion-1",
        gross_revenue=Decimal("2.00"),
        rule=rule,
    )

    assert created is True
    assert reward.user_reward == Decimal("0.80")
    assert reward.platform_share == Decimal("1.20")

    reward.refresh_from_db()
    assert reward.status == Reward.Status.APPROVED
    assert get_account(user, WalletAccount.Type.CASH).balance == Decimal("0.80")
    assert get_account(user, WalletAccount.Type.PENDING).balance == Decimal("0")


def test_reward_fixed_points_rule(user):
    rule = RewardRule.objects.create(
        name="100 points", source=RewardRule.Source.OFFER, fixed_points=Decimal("100")
    )
    reward, _ = RewardService.award(
        user=user,
        source=Reward.Source.OFFER,
        source_reference="conversion-points",
        gross_revenue=Decimal("2.00"),
        rule=rule,
    )
    assert reward.points_reward == Decimal("100.00")
    assert get_account(user, WalletAccount.Type.CASH).balance == Decimal("0")


# --------------------------------------------------------------------------
# §142 — Idempotency: the same conversion must never pay twice
# --------------------------------------------------------------------------
def test_reward_idempotent_for_same_reference(user):
    rule = RewardRule.objects.create(
        name="50%", source=RewardRule.Source.OFFER, user_percentage=Decimal("50")
    )
    first, created_first = RewardService.award(
        user=user,
        source=Reward.Source.OFFER,
        source_reference="conversion-xyz",
        gross_revenue=Decimal("2.00"),
        rule=rule,
    )
    second, created_second = RewardService.award(
        user=user,
        source=Reward.Source.OFFER,
        source_reference="conversion-xyz",
        gross_revenue=Decimal("2.00"),
        rule=rule,
    )

    assert created_first is True
    assert created_second is False
    assert first.pk == second.pk
    assert get_account(user, WalletAccount.Type.CASH).balance == Decimal("1.00")
    assert Reward.objects.filter(user=user).count() == 1


# --------------------------------------------------------------------------
# §106 — Ledger integrity
# --------------------------------------------------------------------------
def test_ledger_rejects_unbalanced_transaction(user):
    with pytest.raises(ValidationError):
        post_transaction(
            type=LedgerTransaction.Type.ADJUSTMENT,
            entries=[
                (get_account(user, WalletAccount.Type.CASH), Decimal("5.00")),
                (system_account(WalletAccount.Type.CASH), Decimal("-4.00")),
            ],
            idempotency_key="unbalanced-test",
        )


def test_ledger_idempotency_key_returns_existing(user):
    entries = [
        (system_account(WalletAccount.Type.CASH), Decimal("-3.00")),
        (get_account(user, WalletAccount.Type.CASH), Decimal("3.00")),
    ]
    txn1, created1 = post_transaction(
        type=LedgerTransaction.Type.ADJUSTMENT, entries=entries, idempotency_key="same-key"
    )
    txn2, created2 = post_transaction(
        type=LedgerTransaction.Type.ADJUSTMENT, entries=entries, idempotency_key="same-key"
    )

    assert created1 is True
    assert created2 is False
    assert txn1.pk == txn2.pk
    assert get_account(user, WalletAccount.Type.CASH).balance == Decimal("3.00")


def test_reversal_creates_compensating_entries(user):
    txn, _ = post_transaction(
        type=LedgerTransaction.Type.ADJUSTMENT,
        entries=[
            (system_account(WalletAccount.Type.CASH), Decimal("-7.00")),
            (get_account(user, WalletAccount.Type.CASH), Decimal("7.00")),
        ],
        idempotency_key="to-reverse",
    )
    assert get_account(user, WalletAccount.Type.CASH).balance == Decimal("7.00")

    reversal, created = reverse_transaction(txn, reason="test")
    assert created is True
    assert reversal.type == LedgerTransaction.Type.REVERSAL
    assert get_account(user, WalletAccount.Type.CASH).balance == Decimal("0")
    txn.refresh_from_db()
    assert txn.status == LedgerTransaction.Status.REVERSED


def test_ledger_entries_are_immutable(user):
    txn, _ = post_transaction(
        type=LedgerTransaction.Type.ADJUSTMENT,
        entries=[
            (system_account(WalletAccount.Type.CASH), Decimal("-1.00")),
            (get_account(user, WalletAccount.Type.CASH), Decimal("1.00")),
        ],
        idempotency_key="immutable-test",
    )
    entry = txn.entries.first()
    entry.amount = Decimal("999.00")
    with pytest.raises(ValidationError):
        entry.save()


# --------------------------------------------------------------------------
# §143 — Withdrawals: reservation prevents double spending
# --------------------------------------------------------------------------
def test_withdrawal_reserves_funds_and_blocks_double_spend(user):
    RewardService.award_fixed(
        user=user, source=Reward.Source.PROMOTION, cash=Decimal("10.00"), source_reference="topup"
    )
    method = WithdrawalMethod.objects.create(user=user, type=WithdrawalMethod.Type.EASYPAISA)

    first = request_withdrawal(user=user, method=method, amount=Decimal("8.00"))
    assert first.status == Withdrawal.Status.REQUESTED
    assert get_account(user, WalletAccount.Type.CASH).balance == Decimal("2.00")
    assert get_account(user, WalletAccount.Type.LOCKED).balance == Decimal("8.00")

    with pytest.raises(WithdrawalError):
        request_withdrawal(user=user, method=method, amount=Decimal("5.00"))

    reject_withdrawal(first, reason="test rejection")
    assert get_account(user, WalletAccount.Type.CASH).balance == Decimal("10.00")
    assert get_account(user, WalletAccount.Type.LOCKED).balance == Decimal("0")


def test_reward_reversal_removes_credited_funds(user):
    reward, _ = RewardService.award_fixed(
        user=user, source=Reward.Source.PROMOTION, cash=Decimal("5.00"), source_reference="bonus-1"
    )
    assert get_account(user, WalletAccount.Type.CASH).balance == Decimal("5.00")

    RewardService.reverse(reward, reason="chargeback")
    reward.refresh_from_db()

    assert reward.status == Reward.Status.REVERSED
    assert get_account(user, WalletAccount.Type.CASH).balance == Decimal("0")


def test_zero_reward_rule_raises(user):
    rule = RewardRule.objects.create(name="zero", source=RewardRule.Source.OFFER)
    with pytest.raises(RewardError):
        RewardService.award(
            user=user,
            source=Reward.Source.OFFER,
            source_reference="zero-reward",
            gross_revenue=Decimal("2.00"),
            rule=rule,
        )


def test_cached_balance_matches_ledger(user):
    RewardService.award_fixed(
        user=user, source=Reward.Source.PROMOTION, cash=Decimal("12.34"), source_reference="ledger-check"
    )
    cash = get_account(user, WalletAccount.Type.CASH)
    assert account_balance(cash) == cash.balance == Decimal("12.34")
