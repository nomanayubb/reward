"""User profile, security, device, session, risk profile and restrictions."""
from django.conf import settings
from django.db import models

from apps.common.models import TimeStampedModel, UUIDTimeStampedModel


class UserProfile(UUIDTimeStampedModel):
    class Tier(models.TextChoices):
        BRONZE = "bronze", "Bronze"
        SILVER = "silver", "Silver"
        GOLD = "gold", "Gold"
        PLATINUM = "platinum", "Platinum"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile"
    )
    display_name = models.CharField(max_length=80, blank=True)
    avatar = models.ImageField(upload_to="avatars/", null=True, blank=True)
    country = models.CharField(max_length=2, blank=True)
    language = models.CharField(max_length=8, default="en")
    timezone = models.CharField(max_length=64, default="Asia/Karachi")

    tier = models.CharField(max_length=16, choices=Tier.choices, default=Tier.BRONZE, db_index=True)
    xp = models.PositiveIntegerField(default=0)
    level = models.PositiveIntegerField(default=1)

    date_of_birth = models.DateField(null=True, blank=True)
    address = models.CharField(max_length=255, blank=True)

    class Meta:
        indexes = [models.Index(fields=["tier", "level"])]

    def __str__(self):
        return f"profile:{self.user_id}"


class UserSecurity(UUIDTimeStampedModel):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="security"
    )
    two_factor_enabled = models.BooleanField(default=False)
    two_factor_secret = models.CharField(max_length=128, blank=True)
    last_password_change = models.DateTimeField(null=True, blank=True)
    failed_login_attempts = models.PositiveIntegerField(default=0)
    locked_until = models.DateTimeField(null=True, blank=True)
    password_reset_token_hash = models.CharField(max_length=128, blank=True)
    email_verification_token_hash = models.CharField(max_length=128, blank=True)

    def __str__(self):
        return f"security:{self.user_id}"


class UserDevice(UUIDTimeStampedModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="devices"
    )
    device_id_hash = models.CharField(max_length=128, db_index=True)
    browser_family = models.CharField(max_length=64, blank=True)
    os_family = models.CharField(max_length=64, blank=True)
    screen = models.CharField(max_length=32, blank=True)
    timezone = models.CharField(max_length=64, blank=True)
    language = models.CharField(max_length=16, blank=True)
    last_ip = models.GenericIPAddressField(null=True, blank=True)
    risk_flags = models.JSONField(default=dict, blank=True)
    is_trusted = models.BooleanField(default=False)
    last_seen_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "device_id_hash"], name="uniq_user_device"
            )
        ]
        indexes = [models.Index(fields=["device_id_hash"])]

    def __str__(self):
        return f"device:{self.device_id_hash[:12]}"


class UserSession(UUIDTimeStampedModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="login_sessions"
    )
    session_key = models.CharField(max_length=64, db_index=True)
    device = models.ForeignKey(
        UserDevice, null=True, blank=True, on_delete=models.SET_NULL, related_name="sessions"
    )
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=255, blank=True)
    started_at = models.DateTimeField(auto_now_add=True)
    last_activity_at = models.DateTimeField(auto_now=True)
    revoked_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-started_at"]

    def __str__(self):
        return f"session:{self.user_id}"


class UserRiskProfile(UUIDTimeStampedModel):
    class Level(models.TextChoices):
        LOW = "low", "Low"
        MEDIUM = "medium", "Medium"
        HIGH = "high", "High"
        CRITICAL = "critical", "Critical"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="risk_profile"
    )
    risk_score = models.PositiveSmallIntegerField(default=0)
    level = models.CharField(max_length=16, choices=Level.choices, default=Level.LOW, db_index=True)
    signals = models.JSONField(default=dict, blank=True)
    last_evaluated_at = models.DateTimeField(null=True, blank=True)
    review_required = models.BooleanField(default=False)

    @staticmethod
    def level_for_score(score: int) -> str:
        if score <= 20:
            return UserRiskProfile.Level.LOW
        if score <= 50:
            return UserRiskProfile.Level.MEDIUM
        if score <= 75:
            return UserRiskProfile.Level.HIGH
        return UserRiskProfile.Level.CRITICAL

    def __str__(self):
        return f"risk:{self.user_id}:{self.risk_score}"


class UserRestriction(UUIDTimeStampedModel):
    class Type(models.TextChoices):
        GAME_DISABLED = "game_disabled", "Games disabled"
        SURVEY_DISABLED = "survey_disabled", "Surveys disabled"
        OFFERS_DISABLED = "offers_disabled", "Offers disabled"
        WITHDRAWAL_DISABLED = "withdrawal_disabled", "Withdrawals disabled"
        DEPOSIT_DISABLED = "deposit_disabled", "Deposits disabled"
        REFERRAL_DISABLED = "referral_disabled", "Referrals disabled"
        BONUS_DISABLED = "bonus_disabled", "Bonuses disabled"
        LOGIN_DISABLED = "login_disabled", "Login disabled"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="restrictions"
    )
    type = models.CharField(max_length=32, choices=Type.choices, db_index=True)
    reason = models.CharField(max_length=255, blank=True)
    until = models.DateTimeField(null=True, blank=True, help_text="Blank = permanent")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="restrictions_created",
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        indexes = [models.Index(fields=["user", "type", "is_active"])]

    def __str__(self):
        return f"{self.type}:{self.user_id}"
