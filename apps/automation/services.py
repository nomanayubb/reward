"""Automation engine: internal event bus + trigger/condition/action rules."""
import logging

from django.db import transaction
from django.utils import timezone

from .models import AutomationExecution, AutomationRule

logger = logging.getLogger(__name__)


@transaction.atomic
def emit_event(event_name: str, user=None, payload: dict | None = None) -> list[AutomationExecution]:
    """Dispatch an internal event (e.g. OFFER_CONVERTED) to matching rules."""
    payload = payload or {}
    trigger = event_name.lower()
    executions: list[AutomationExecution] = []

    rules = AutomationRule.objects.filter(is_active=True, trigger=trigger).order_by("priority")
    for rule in rules:
        if rule.max_executions_per_user is not None and user is not None:
            used = AutomationExecution.objects.filter(
                rule=rule, user=user, status=AutomationExecution.Status.SUCCESS
            ).count()
            if used >= rule.max_executions_per_user:
                executions.append(
                    AutomationExecution.objects.create(
                        rule=rule,
                        user=user,
                        status=AutomationExecution.Status.SKIPPED,
                        event_payload=payload,
                        result={"reason": "max_executions_reached"},
                    )
                )
                continue

        if not _conditions_match(rule.conditions, user, payload):
            executions.append(
                AutomationExecution.objects.create(
                    rule=rule,
                    user=user,
                    status=AutomationExecution.Status.SKIPPED,
                    event_payload=payload,
                    result={"reason": "conditions_not_met"},
                )
            )
            continue

        try:
            result = _run_actions(rule, user, payload)
            executions.append(
                AutomationExecution.objects.create(
                    rule=rule,
                    user=user,
                    status=AutomationExecution.Status.SUCCESS,
                    event_payload=payload,
                    result=result,
                )
            )
        except Exception as exc:  # never let automation break the caller's flow
            logger.exception("Automation rule %s failed", rule.pk)
            executions.append(
                AutomationExecution.objects.create(
                    rule=rule,
                    user=user,
                    status=AutomationExecution.Status.FAILED,
                    event_payload=payload,
                    error=str(exc)[:255],
                )
            )
    return executions


def _conditions_match(conditions: dict, user, payload: dict) -> bool:
    if not conditions:
        return True

    if user is not None:
        risk_score = getattr(getattr(user, "risk_profile", None), "risk_score", 0) or 0
        if "risk_lt" in conditions and not risk_score < int(conditions["risk_lt"]):
            return False
        if "risk_gte" in conditions and not risk_score >= int(conditions["risk_gte"]):
            return False

        account_age_days = (timezone.now() - user.date_joined).days
        if "account_age_days_gte" in conditions and not account_age_days >= int(conditions["account_age_days_gte"]):
            return False
        if "account_age_days_lt" in conditions and not account_age_days < int(conditions["account_age_days_lt"]):
            return False

    for key, expected in (conditions.get("payload_equals") or {}).items():
        if str(payload.get(key)) != str(expected):
            return False

    return True


def _run_actions(rule: AutomationRule, user, payload: dict) -> dict:
    results = {}
    for item in rule.actions or []:
        action = item.get("action")
        params = item.get("params", {}) or {}
        results[action] = _run_action(action, params, user, payload)
    return results


def _run_action(action: str, params: dict, user, payload: dict):
    from apps.notifications.services import notify
    from apps.rewards.models import Reward
    from apps.rewards.services import RewardService

    if action == AutomationRule.Action.CREDIT_POINTS:
        if user is None:
            return "skipped:no_user"
        RewardService.award_fixed(
            user=user,
            source=Reward.Source.PROMOTION,
            source_reference=params.get("reference", "") or "",
            points=params.get("points", 0),
            context={"automation": True, "params": params},
        )
        return "credited"

    if action == AutomationRule.Action.CREDIT_CASH:
        if user is None:
            return "skipped:no_user"
        RewardService.award_fixed(
            user=user,
            source=Reward.Source.PROMOTION,
            source_reference=params.get("reference", "") or "",
            cash=params.get("cash", 0),
            context={"automation": True, "params": params},
        )
        return "credited"

    if action == AutomationRule.Action.SEND_NOTIFICATION:
        if user is None:
            return "skipped:no_user"
        notify(
            user,
            kind=params.get("kind", "system"),
            title=params.get("title", "Notification"),
            body=params.get("body", ""),
        )
        return "sent"

    if action == AutomationRule.Action.SEND_EMAIL:
        if user is None:
            return "skipped:no_user"
        from apps.notifications.services import send_email_template

        send_email_template(
            params.get("template", "system"),
            user,
            context=params.get("context", {}),
            fallback_subject=params.get("title", "Notification"),
            fallback_body=params.get("body", ""),
        )
        return "sent"

    if action == AutomationRule.Action.FREEZE_ACCOUNT:
        if user is None:
            return "skipped:no_user"
        user.status = user.Status.FROZEN
        user.save(update_fields=["status", "updated_at"])
        return "frozen"

    if action == AutomationRule.Action.CHANGE_TIER:
        if user is None:
            return "skipped:no_user"
        profile = getattr(user, "profile", None)
        if profile is not None and params.get("tier"):
            profile.tier = params["tier"]
            profile.save(update_fields=["tier", "updated_at"])
            return "tier_changed"
        return "skipped:no_profile"

    if action in {AutomationRule.Action.DISABLE_OFFER, AutomationRule.Action.ENABLE_OFFER}:
        from apps.offers.models import Offer

        offer = Offer.objects.filter(pk=params.get("offer_id")).first()
        if offer is None:
            return "skipped:offer_not_found"
        offer.status = Offer.Status.PAUSED if action.endswith("disable_offer") else Offer.Status.ACTIVE
        offer.save(update_fields=["status", "updated_at"])
        return offer.status

    if action == AutomationRule.Action.PAUSE_CAMPAIGN:
        from apps.offers.models import Offer

        offer = Offer.objects.filter(pk=params.get("offer_id")).first()
        if offer is None:
            return "skipped:offer_not_found"
        offer.status = Offer.Status.PAUSED
        offer.save(update_fields=["status", "updated_at"])
        return "paused"

    if action == AutomationRule.Action.CREATE_ADMIN_ALERT:
        logger.warning("ADMIN ALERT [%s]: %s", params.get("level", "info"), params.get("message", ""))
        return "alerted"

    return f"unhandled:{action}"
