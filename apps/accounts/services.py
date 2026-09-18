"""Account services: registration, referral codes, verification tokens."""
import secrets
import uuid

from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone

REFERRAL_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
REFERRAL_LENGTH = 8


def generate_referral_code(length: int = REFERRAL_LENGTH) -> str:
    User = get_user_model()
    while True:
        code = "".join(secrets.choice(REFERRAL_ALPHABET) for _ in range(length))
        if not User.objects.filter(referral_code=code).exists():
            return code


def generate_token(length: int = 32) -> str:
    return secrets.token_urlsafe(length)


def player_id_for(user) -> str:
    """Stable, provider-safe player id.

    AdGem requires: lowercase, alphanumeric + hyphens/underscores, max 255
    characters, and a value that is constant per user (so they can prevent
    duplicate completions and attribute rewards). ``u<uuid-hex>`` satisfies all
    of that and is reversible on our side.
    """
    return f"u{user.id.hex}"


def user_for_player_id(player_id: str):
    """Reverse ``player_id_for``; returns ``None`` for foreign ids."""
    value = (player_id or "").strip().lower()
    if not value.startswith("u") or len(value) != 33:
        return None
    try:
        user_uuid = uuid.UUID(hex=value[1:])
    except ValueError:
        return None
    return get_user_model().objects.filter(id=user_uuid).first()


@transaction.atomic
def register_user(*, email: str, password: str, username: str | None = None, referral_code: str = ""):
    """Create a user, their wallet accounts and a referral link when applicable."""
    from apps.wallets.services import get_wallet

    User = get_user_model()
    user = User.objects.create_user(email=email, password=password, username=username)
    get_wallet(user)

    if referral_code:
        from apps.referrals.services import attach_referral

        attach_referral(user, referral_code)

    return user


def mark_email_verified(user) -> None:
    user.is_email_verified = True
    user.email_verified_at = timezone.now()
    user.save(update_fields=["is_email_verified", "email_verified_at", "updated_at"])


def mark_phone_verified(user) -> None:
    user.is_phone_verified = True
    user.phone_verified_at = timezone.now()
    user.save(update_fields=["is_phone_verified", "phone_verified_at", "updated_at"])
