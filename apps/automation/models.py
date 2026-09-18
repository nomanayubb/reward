"""Automation engine: Trigger -> Condition -> Action rules.

Example: WHEN user completes 10 offers, IF risk < 30, THEN credit 100 bonus
points. Rules listen to internal events (apps/automation/events.py).
"""
from django.conf import settings
from django.db import models

from apps.common.models import UUIDTimeStampedModel


class AutomationRule(UUIDTimeStampedModel):
    class Trigger(models.TextChoices):
        USER_REGISTERED = "user_registered", "User registered"
        EMAIL_VERIFIED = "email_verified", "Email verified"
        PHONE_VERIFIED = "phone_verified", "Phone verified"
        FIRST_DEPOSIT = "first_deposit", "First deposit"
        FIRST_GAME = "first_game", "First game"
        GAME_MILESTONE = "game_milestone", "Game milestone"
        SURVEY_COMPLETED = "survey_completed", "Survey completed"
        OFFER_COMPLETED = "offer_completed", "Offer completed"
        WITHDRAWAL_REQUESTED = "withdrawal_requested", "Withdrawal requested"
        WITHDRAWAL_APPROVED = "withdrawal_approved", "Withdrawal approved"
        WITHDRAWAL_REJECTED = "withdrawal_rejected", "Withdrawal rejected"
        REFERRAL_REGISTERED = "referral_registered", "Referral registered"
        REFERRAL_CONVERTED = "referral_converted", "Referral converted"
        FRAUD_SCORE_CHANGED = "fraud_score_changed", "Fraud score changed"
        CAMPAIGN_QUOTA_REACHED = "campaign_quota_reached", "Campaign quota reached"
        PROVIDER_UNAVAILABLE = "provider_unavailable", "Provider unavailable"

    class Action(models.TextChoices):
        CREDIT_POINTS = "credit_points", "Credit points"
        CREDIT_CASH = "credit_cash", "Credit cash"
        SEND_EMAIL = "send_email", "Send email"
        SEND_NOTIFICATION = "send_notification", "Send notification"
        SEND_SMS = "send_sms", "Send SMS"
        FREEZE_ACCOUNT = "freeze_account", "Freeze account"
        HOLD_REWARD = "hold_reward", "Hold reward"
        APPROVE_WITHDRAWAL = "approve_withdrawal", "Approve withdrawal"
        REJECT_WITHDRAWAL = "reject_withdrawal", "Reject withdrawal"
        CHANGE_TIER = "change_tier", "Change user tier"
        DISABLE_OFFER = "disable_offer", "Disable offer"
        ENABLE_OFFER = "enable_offer", "Enable offer"
        PAUSE_CAMPAIGN = "pause_campaign", "Pause campaign"
        CREATE_ADMIN_ALERT = "create_admin_alert", "Create admin alert"

    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True, db_index=True)
    priority = models.PositiveIntegerField(default=100)

    trigger = models.CharField(max_length=32, choices=Trigger.choices, db_index=True)
    conditions = models.JSONField(
        default=dict, blank=True, help_text="AND-ed conditions, e.g. {'risk_lt': 30}"
    )
    actions = models.JSONField(
        default=list, blank=True,
        help_text='List of {"action": "...", "params": {...}} executed in order.',
    )
    max_executions_per_user = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        ordering = ["priority", "name"]

    def __str__(self):
        return f"{self.name} [{self.trigger}]"


class AutomationExecution(UUIDTimeStampedModel):
    class Status(models.TextChoices):
        SUCCESS = "success", "Success"
        SKIPPED = "skipped", "Skipped"
        FAILED = "failed", "Failed"

    rule = models.ForeignKey(
        AutomationRule, on_delete=models.CASCADE, related_name="executions"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="automation_executions",
    )
    status = models.CharField(max_length=16, choices=Status.choices, db_index=True)
    event_payload = models.JSONField(default=dict, blank=True)
    result = models.JSONField(default=dict, blank=True)
    error = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"automation:{self.rule_id}:{self.status}"
