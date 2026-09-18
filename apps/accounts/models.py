"""Accounts: the custom user model and authentication primitives.

The user is identified by email. Everything financial hangs off this model
through ``wallets`` / ``ledger``; never store balances on the user.
"""
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone

from apps.common.models import UUIDTimeStampedModel


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("An email address is required.")
        email = self.normalize_email(email).lower()
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")
        return self._create_user(email, password, **extra_fields)


class User(UUIDTimeStampedModel, AbstractBaseUser, PermissionsMixin):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        INACTIVE = "inactive", "Inactive"
        SUSPENDED = "suspended", "Suspended"
        FROZEN = "frozen", "Frozen"
        CLOSED = "closed", "Closed"

    email = models.EmailField(unique=True)
    username = models.CharField(max_length=50, unique=True, null=True, blank=True)
    phone = models.CharField(max_length=32, blank=True)
    country = models.CharField(max_length=2, default="PK")

    status = models.CharField(
        max_length=16, choices=Status.choices, default=Status.ACTIVE, db_index=True
    )
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    is_email_verified = models.BooleanField(default=False)
    is_phone_verified = models.BooleanField(default=False)
    email_verified_at = models.DateTimeField(null=True, blank=True)
    phone_verified_at = models.DateTimeField(null=True, blank=True)

    referral_code = models.CharField(max_length=16, unique=True, blank=True)

    date_joined = models.DateTimeField(default=timezone.now, db_index=True)
    last_seen_at = models.DateTimeField(null=True, blank=True)
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS: list[str] = []

    class Meta:
        verbose_name = "user"
        verbose_name_plural = "users"
        indexes = [
            models.Index(fields=["status", "date_joined"]),
            models.Index(fields=["country", "status"]),
        ]

    def __str__(self):
        return self.email

    def save(self, *args, **kwargs):
        if not self.referral_code:
            from apps.accounts.services import generate_referral_code

            self.referral_code = generate_referral_code()
        super().save(*args, **kwargs)

    def get_full_name(self):
        profile = getattr(self, "profile", None)
        if profile and profile.display_name:
            return profile.display_name
        return self.username or self.email

    def get_short_name(self):
        return self.username or self.email.split("@")[0]

    @property
    def is_frozen(self):
        return self.status in {self.Status.FROZEN, self.Status.SUSPENDED, self.Status.CLOSED}
