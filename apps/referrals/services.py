"""Referral services: attaching referrers and recording qualified conversions."""
import logging
from decimal import Decimal

from django.db import transaction

from apps.rewards.models import Reward

from .models import Referral, ReferralConversion

logger = logging.getLogger(__name__)


@transaction.atomic
def attach_referral(user, code: str) -> Referral | None:
    """Link a new user to the owner of ``code``, applying basic fraud checks."""
    from django.contrib.auth import get_user_model

    User = get_user_model()
    code = (code or "").strip().upper()
    if not code:
        return None

    referrer = User.objects.filter(referral_code=code, is_active=True).first()
    if referrer is None or referrer.pk == user.pk:
        return None

    fraud_flags = {}
    if user.last_login_ip and referrer.last_login_ip and user.last_login_ip == referrer.last_login_ip:
        fraud_flags["same_ip"] = True
    if fraud_flags:
        logger.warning("Referral %s flagged: %s", user.pk, fraud_flags)

    referral, _ = Referral.objects.get_or_create(
        referred=user,
        defaults={
            "referrer": referrer,
            "code_used": code,
            "signup_ip": user.last_login_ip,
            "fraud_flags": fraud_flags,
            "status": Referral.Status.REJECTED if fraud_flags else Referral.Status.REGISTERED,
        },
    )
    return referral


@transaction.atomic
def record_conversion(
    referral: Referral, *, source: str, source_reference: str = "", gross_amount=Decimal("0")
) -> ReferralConversion:
    """Create a referral conversion record for the reward engine to price."""
    from apps.adminpanel.settings import get_setting

    percentage = Decimal(str(get_setting("REFERRAL_PERCENTAGE", 10)))
    reward_amount = (Decimal(str(gross_amount)) * percentage / Decimal("100")).quantize(
        Decimal("0.00000001")
    )

    conversion = ReferralConversion.objects.create(
        referral=referral,
        source=source,
        source_reference=source_reference,
        gross_amount=gross_amount,
        reward_amount=reward_amount,
        status=ReferralConversion.Status.PENDING,
    )

    if reward_amount > 0:
        from apps.rewards.services import RewardService

        reward = RewardService.award(
            user=referral.referrer,
            source=Reward.Source.REFERRAL,
            source_reference=f"{conversion.id}",
            gross_revenue=gross_amount,
            context={"source": "referral"},
        )
        conversion.reward = reward
        conversion.save(update_fields=["reward", "updated_at"])

    referral.status = Referral.Status.QUALIFIED
    referral.save(update_fields=["status", "updated_at"])
    return conversion
