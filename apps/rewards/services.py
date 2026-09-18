"""Reward engine (docs/DRD.md §25-28, §92).

One place decides what a user earns. Games, surveys, CPA conversions, bonuses
and referrals all go through ``RewardService`` so accounting stays consistent.

Flow: validated revenue -> RewardRule -> pending bucket -> approval -> wallet.
"""
import logging
from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from apps.ledger import services as ledger
from apps.ledger.models import LedgerTransaction
from apps.payments.services import convert
from apps.wallets.models import WalletAccount
from apps.wallets.services import (
    get_account,
    points_account,
    system_account,
    system_pending_points_account,
    system_points_account,
)

from .models import Reward, RewardRule

logger = logging.getLogger(__name__)

ZERO = Decimal("0")
MONEY_QUANT = Decimal("0.00000001")
POINTS_QUANT = Decimal("0.01")

DEFAULT_REWARD_CURRENCY = "PKR"
DEFAULT_REVENUE_CURRENCY = "USD"


class RewardError(Exception):
    """Raised when a reward cannot be created or transitioned."""


# --------------------------------------------------------------------------
# Rule resolution + calculation
# --------------------------------------------------------------------------
def _conditions_match(conditions: dict, *, payout=None) -> bool:
    if not conditions:
        return True

    min_payout = conditions.get("min_payout")
    max_payout = conditions.get("max_payout")
    if min_payout is None and max_payout is None:
        return True
    if payout is None:
        return False

    payout = Decimal(str(payout))
    if min_payout is not None and payout < Decimal(str(min_payout)):
        return False
    return max_payout is None or payout <= Decimal(str(max_payout))


def resolve_rule(
    *,
    source: str,
    provider_code: str = "",
    campaign_type: str = "",
    country: str = "",
    user_tier: str = "",
    payout=None,
) -> RewardRule | None:
    """First active rule (by priority) whose scope matches the context."""
    rules = RewardRule.objects.filter(is_active=True).order_by("priority", "created_at")
    for rule in rules:
        if rule.source not in (RewardRule.Source.ANY, source):
            continue
        if rule.provider_code and rule.provider_code != provider_code:
            continue
        if rule.campaign_type and rule.campaign_type != campaign_type:
            continue
        if rule.country and rule.country != country:
            continue
        if rule.user_tier and rule.user_tier != user_tier:
            continue
        if not _conditions_match(rule.conditions, payout=payout):
            continue
        return rule
    return None


def calculate_reward_parts(
    rule: RewardRule | None, payout
) -> tuple[Decimal, Decimal, Decimal]:
    """Return ``(percentage_cash, fixed_cash, points)`` before conversion.

    ``percentage_cash`` is denominated in the revenue currency; ``fixed_cash``
    is already denominated in the rule's reward currency.
    """
    if rule is None:
        return ZERO, ZERO, ZERO

    payout = Decimal(str(payout or 0))
    percentage_cash, fixed_cash, points = ZERO, ZERO, ZERO

    if rule.user_percentage is not None:
        percentage_cash += payout * rule.user_percentage / Decimal("100")
    if rule.fixed_cash is not None:
        fixed_cash += rule.fixed_cash
    if rule.points_percentage is not None:
        points += payout * rule.points_percentage / Decimal("100")
    if rule.fixed_points is not None:
        points += rule.fixed_points
    if rule.multiplier and rule.multiplier != 1:
        percentage_cash *= rule.multiplier
        fixed_cash *= rule.multiplier
        points *= rule.multiplier

    return percentage_cash, fixed_cash, points.quantize(POINTS_QUANT)


# --------------------------------------------------------------------------
# Service
# --------------------------------------------------------------------------
class RewardService:
    """All money-in for users flows through here."""

    @classmethod
    @transaction.atomic
    def award(
        cls,
        *,
        user,
        source: str,
        source_reference: str = "",
        gross_revenue=None,
        rule: RewardRule | None = None,
        context: dict | None = None,
        auto_approve: bool | None = None,
    ) -> tuple[Reward, bool]:
        """Create a reward, credit the pending bucket and optionally approve."""
        context = context or {}

        if source_reference:
            existing = Reward.objects.filter(
                source=source, source_reference=source_reference, user=user
            ).first()
            if existing:
                return existing, False

        if rule is None:
            rule = resolve_rule(
                source=source,
                provider_code=context.get("provider_code", ""),
                campaign_type=context.get("campaign_type", ""),
                country=context.get("country", getattr(user, "country", "") or ""),
                user_tier=context.get("user_tier", ""),
                payout=gross_revenue,
            )

        reward_currency = context.get("reward_currency") or (
            rule.reward_currency if rule is not None else DEFAULT_REWARD_CURRENCY
        )
        revenue_currency = context.get("revenue_currency", DEFAULT_REVENUE_CURRENCY)

        percentage_cash, fixed_cash, points = calculate_reward_parts(rule, gross_revenue)
        exchange_rate = None
        if percentage_cash and revenue_currency != reward_currency:
            percentage_cash, exchange_rate = convert(
                percentage_cash, revenue_currency, reward_currency
            )

        cash = (percentage_cash + fixed_cash).quantize(MONEY_QUANT)
        if rule is not None and rule.max_user_reward is not None and cash > rule.max_user_reward:
            cash = rule.max_user_reward

        # Platform share stays in the revenue currency so profitability math
        # never mixes currencies.
        platform_share = None
        if gross_revenue is not None:
            if revenue_currency == reward_currency:
                cash_in_revenue = cash
            else:
                cash_in_revenue, _ = convert(cash, reward_currency, revenue_currency)
            platform_share = Decimal(str(gross_revenue)) - cash_in_revenue

        if exchange_rate is not None:
            context = {
                **context,
                "revenue_currency": revenue_currency,
                "exchange_rate": str(exchange_rate),
            }

        return cls._issue(
            user=user,
            source=source,
            source_reference=source_reference,
            cash=cash,
            points=points,
            gross_revenue=gross_revenue,
            platform_share=platform_share,
            rule=rule,
            reward_currency=reward_currency,
            revenue_currency=revenue_currency,
            context=context,
            auto_approve=auto_approve,
        )

    @classmethod
    @transaction.atomic
    def award_fixed(
        cls,
        *,
        user,
        source: str,
        source_reference: str = "",
        cash=ZERO,
        points=ZERO,
        currency: str = DEFAULT_REWARD_CURRENCY,
        gross_revenue=None,
        context: dict | None = None,
        auto_approve: bool | None = True,
    ) -> tuple[Reward, bool]:
        """Award explicitly configured amounts (game rules, bonuses, admin grants)."""
        return cls._issue(
            user=user,
            source=source,
            source_reference=source_reference,
            cash=Decimal(str(cash)).quantize(MONEY_QUANT),
            points=Decimal(str(points)).quantize(POINTS_QUANT),
            gross_revenue=gross_revenue,
            rule=None,
            reward_currency=currency,
            context=context or {},
            auto_approve=auto_approve,
        )

    @classmethod
    def _issue(
        cls,
        *,
        user,
        source: str,
        source_reference: str,
        cash: Decimal,
        points: Decimal,
        gross_revenue=None,
        platform_share=None,
        rule: RewardRule | None = None,
        reward_currency: str = DEFAULT_REWARD_CURRENCY,
        revenue_currency: str | None = None,
        context: dict | None = None,
        auto_approve: bool | None = None,
    ) -> tuple[Reward, bool]:
        context = context or {}

        if source_reference:
            existing = Reward.objects.filter(
                source=source, source_reference=source_reference, user=user
            ).first()
            if existing:
                return existing, False

        if cash <= 0 and points <= 0:
            raise RewardError("Reward resolves to zero — check RewardRule configuration.")

        if (
            gross_revenue is not None
            and revenue_currency == reward_currency
            and cash > Decimal(str(gross_revenue))
        ):
            logger.warning(
                "Reward %s exceeds gross revenue %s (user=%s rule=%s) — verify admin config.",
                cash,
                gross_revenue,
                user.pk,
                getattr(rule, "pk", None),
            )

        reward = Reward.objects.create(
            user=user,
            source=source,
            source_reference=source_reference,
            rule=rule,
            gross_revenue=gross_revenue,
            platform_share=platform_share,
            user_reward=cash,
            points_reward=points,
            currency=reward_currency,
            status=Reward.Status.PENDING,
            metadata=context,
        )

        if cash > 0:
            txn, _ = ledger.post_transaction(
                type=LedgerTransaction.Type.REWARD,
                entries=[
                    (system_account(WalletAccount.Type.CASH, reward_currency), -cash),
                    (get_account(user, WalletAccount.Type.PENDING, reward_currency), cash),
                ],
                reference=str(reward.id),
                description=f"Pending {source} reward",
                metadata={
                    "reward_id": str(reward.id),
                    "user_id": str(user.pk),
                    "currency": reward_currency,
                },
                idempotency_key=f"reward:{reward.id}:pending",
            )
            reward.ledger_transaction = txn

        if points > 0:
            ledger.post_transaction(
                type=LedgerTransaction.Type.REWARD,
                entries=[
                    (system_points_account(), -points),
                    (system_pending_points_account(), points),
                ],
                reference=str(reward.id),
                description=f"Pending {source} points",
                metadata={"reward_id": str(reward.id), "user_id": str(user.pk)},
                idempotency_key=f"reward:{reward.id}:pending:points",
            )

        reward.save(update_fields=["ledger_transaction", "updated_at"])

        should_auto = auto_approve
        if should_auto is None:
            should_auto = not (rule is not None and rule.requires_manual_approval)
        if should_auto:
            cls.approve(reward)

        return reward, True

    @classmethod
    @transaction.atomic
    def approve(cls, reward: Reward, *, approved_by=None) -> Reward:
        reward = Reward.objects.select_for_update().get(pk=reward.pk)
        if reward.status == Reward.Status.APPROVED:
            return reward
        if reward.status != Reward.Status.PENDING:
            raise RewardError(f"Cannot approve a reward in status '{reward.status}'.")

        if reward.user_reward > 0:
            txn, _ = ledger.post_transaction(
                type=LedgerTransaction.Type.REWARD,
                entries=[
                    (
                        get_account(reward.user, WalletAccount.Type.PENDING, reward.currency),
                        -reward.user_reward,
                    ),
                    (
                        get_account(reward.user, WalletAccount.Type.CASH, reward.currency),
                        reward.user_reward,
                    ),
                ],
                reference=str(reward.id),
                description="Reward approved",
                metadata={"reward_id": str(reward.id), "user_id": str(reward.user_id)},
                idempotency_key=f"reward:{reward.id}:approve",
            )
            reward.ledger_transaction = txn

        if reward.points_reward > 0:
            ledger.post_transaction(
                type=LedgerTransaction.Type.REWARD,
                entries=[
                    (system_pending_points_account(), -reward.points_reward),
                    (points_account(reward.user), reward.points_reward),
                ],
                reference=str(reward.id),
                description="Points reward approved",
                metadata={"reward_id": str(reward.id), "user_id": str(reward.user_id)},
                idempotency_key=f"reward:{reward.id}:approve:points",
            )

        reward.status = Reward.Status.APPROVED
        reward.approved_at = timezone.now()
        reward.approved_by = approved_by
        reward.save(
            update_fields=["status", "approved_at", "approved_by", "ledger_transaction", "updated_at"]
        )
        return reward

    @classmethod
    @transaction.atomic
    def hold(cls, reward: Reward, *, reason: str = "") -> Reward:
        reward = Reward.objects.select_for_update().get(pk=reward.pk)
        if reward.status != Reward.Status.PENDING:
            raise RewardError("Only pending rewards can be held for review.")
        reward.metadata = {**(reward.metadata or {}), "held": True, "hold_reason": reason}
        reward.save(update_fields=["metadata", "updated_at"])
        return reward

    @classmethod
    @transaction.atomic
    def reject(cls, reward: Reward, *, rejected_by=None, reason: str = "") -> Reward:
        reward = Reward.objects.select_for_update().get(pk=reward.pk)
        if reward.status != Reward.Status.PENDING:
            raise RewardError("Only pending rewards can be rejected.")
        cls._reverse_pending(reward, reason=reason or "Reward rejected")
        reward.status = Reward.Status.REJECTED
        reward.metadata = {**(reward.metadata or {}), "reject_reason": reason}
        reward.save(update_fields=["status", "metadata", "updated_at"])
        return reward

    @classmethod
    @transaction.atomic
    def reverse(cls, reward: Reward, *, reversed_by=None, reason: str = "") -> Reward:
        """Reverse an approved or pending reward without deleting history."""
        reward = Reward.objects.select_for_update().get(pk=reward.pk)
        if reward.status == Reward.Status.REVERSED:
            return reward
        if reward.status not in {Reward.Status.PENDING, Reward.Status.APPROVED}:
            raise RewardError(f"Cannot reverse a reward in status '{reward.status}'.")

        if reward.status == Reward.Status.PENDING:
            cls._reverse_pending(reward, reason=reason or "Reward reversed")
        else:
            cls._reverse_by_keys(
                reward,
                (
                    f"reward:{reward.id}:approve",
                    f"reward:{reward.id}:approve:points",
                    f"reward:{reward.id}:pending",
                    f"reward:{reward.id}:pending:points",
                ),
                reason=reason or "Reward reversed",
            )

        reward.status = Reward.Status.REVERSED
        reward.metadata = {**(reward.metadata or {}), "reversal_reason": reason}
        reward.save(update_fields=["status", "metadata", "updated_at"])
        return reward

    @staticmethod
    def _reverse_pending(reward: Reward, *, reason: str) -> None:
        RewardService._reverse_by_keys(
            reward,
            (f"reward:{reward.id}:pending", f"reward:{reward.id}:pending:points"),
            reason=reason,
        )

    @staticmethod
    def _reverse_by_keys(reward: Reward, keys, *, reason: str) -> None:
        for key in keys:
            txn = LedgerTransaction.objects.filter(idempotency_key=key).first()
            if txn and txn.status != LedgerTransaction.Status.REVERSED:
                ledger.reverse_transaction(txn, reason=reason)
