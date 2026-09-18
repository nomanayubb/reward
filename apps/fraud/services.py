"""Fraud and risk services: event recording, scoring, rule actions."""
import logging

from django.db import transaction
from django.utils import timezone

from apps.risk.models import RiskRule, RiskScore
from apps.users.models import UserRestriction, UserRiskProfile

from .models import FraudEvent

logger = logging.getLogger(__name__)

SEVERITY_WEIGHTS = {
    FraudEvent.Severity.LOW: 5,
    FraudEvent.Severity.MEDIUM: 15,
    FraudEvent.Severity.HIGH: 30,
    FraudEvent.Severity.CRITICAL: 60,
}

OPEN_STATUSES = {FraudEvent.Status.OPEN, FraudEvent.Status.REVIEWING}


@transaction.atomic
def record_fraud_event(
    *,
    user=None,
    kind: str,
    severity: str = FraudEvent.Severity.LOW,
    evidence: dict | None = None,
    ip=None,
    device_hash: str = "",
) -> FraudEvent:
    event = FraudEvent.objects.create(
        user=user,
        kind=kind,
        severity=severity,
        evidence=evidence or {},
        ip_address=ip,
        device_id_hash=device_hash,
    )
    if user is not None:
        recalculate_user_risk(user)
    return event


@transaction.atomic
def recalculate_user_risk(user) -> UserRiskProfile:
    """Recompute the 0-100 risk score from open fraud events and apply rules."""
    profile, _ = UserRiskProfile.objects.select_for_update().get_or_create(user=user)

    events = FraudEvent.objects.filter(user=user, status__in=OPEN_STATUSES)
    score = 0
    reasons: list[str] = []
    for event in events:
        weight = SEVERITY_WEIGHTS.get(event.severity, 5)
        score += weight
        reasons.append(f"{event.kind}({weight})")

    score = min(score, 100)
    profile.risk_score = score
    profile.level = UserRiskProfile.level_for_score(score)
    profile.signals = {"reasons": reasons}
    profile.last_evaluated_at = timezone.now()
    profile.review_required = score >= 51
    profile.save(
        update_fields=["risk_score", "level", "signals", "last_evaluated_at", "review_required", "updated_at"]
    )

    RiskScore.objects.create(user=user, score=score, reasons=reasons, source="recalculate")
    apply_risk_rules(user, score)
    return profile


def apply_risk_rules(user, score: int) -> None:
    """Apply the first matching active rule per action type."""
    from apps.adminpanel.audit import log_action

    account_age_days = (timezone.now() - user.date_joined).days

    for rule in RiskRule.objects.filter(is_active=True).order_by("priority"):
        conditions = rule.conditions or {}
        if "min_score" in conditions and score < int(conditions["min_score"]):
            continue
        if "max_score" in conditions and score > int(conditions["max_score"]):
            continue
        if "account_age_days_lt" in conditions and account_age_days >= int(conditions["account_age_days_lt"]):
            continue
        if "account_age_days_gte" in conditions and account_age_days < int(conditions["account_age_days_gte"]):
            continue

        action = rule.action
        if action == RiskRule.Action.FREEZE_ACCOUNT:
            if user.status != user.Status.FROZEN:
                user.status = user.Status.FROZEN
                user.save(update_fields=["status", "updated_at"])
                log_action(actor=None, action="risk.freeze_account", obj=user, reason=rule.name)
        elif action == RiskRule.Action.DISABLE_WITHDRAWALS:
            UserRestriction.objects.get_or_create(
                user=user,
                type=UserRestriction.Type.WITHDRAWAL_DISABLED,
                is_active=True,
                defaults={"reason": rule.name},
            )
        elif action == RiskRule.Action.DISABLE_OFFERS:
            UserRestriction.objects.get_or_create(
                user=user,
                type=UserRestriction.Type.OFFERS_DISABLED,
                is_active=True,
                defaults={"reason": rule.name},
            )
        elif action == RiskRule.Action.ALERT_ADMIN:
            logger.warning(
                "Risk rule '%s' matched user %s (score=%s)", rule.name, user.pk, score
            )


def check_ip_risk(ip: str) -> dict:
    """Placeholder hook for an IP reputation provider (VPN/proxy/TOR)."""
    return {"ip": ip, "is_vpn": False, "is_proxy": False, "is_tor": False, "risk": 0}
