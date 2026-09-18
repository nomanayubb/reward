"""Support tickets and reward disputes ("offer missing reward")."""
from django.conf import settings
from django.db import models

from apps.common.models import UUIDTimeStampedModel


class Ticket(UUIDTimeStampedModel):
    class Category(models.TextChoices):
        PAYMENT = "payment", "Payment issue"
        OFFER = "offer", "Offer issue"
        SURVEY = "survey", "Survey issue"
        ACCOUNT = "account", "Account issue"
        WITHDRAWAL = "withdrawal", "Withdrawal issue"
        TECHNICAL = "technical", "Technical issue"
        OTHER = "other", "Other"

    class Status(models.TextChoices):
        OPEN = "open", "Open"
        PENDING_USER = "pending_user", "Pending user"
        PENDING_STAFF = "pending_staff", "Pending staff"
        RESOLVED = "resolved", "Resolved"
        CLOSED = "closed", "Closed"

    class Priority(models.TextChoices):
        LOW = "low", "Low"
        NORMAL = "normal", "Normal"
        HIGH = "high", "High"
        URGENT = "urgent", "Urgent"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="tickets"
    )
    category = models.CharField(max_length=16, choices=Category.choices, db_index=True)
    subject = models.CharField(max_length=200)
    status = models.CharField(
        max_length=16, choices=Status.choices, default=Status.OPEN, db_index=True
    )
    priority = models.CharField(
        max_length=16, choices=Priority.choices, default=Priority.NORMAL, db_index=True
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="tickets_assigned",
    )
    closed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["status", "priority", "created_at"])]

    def __str__(self):
        return f"ticket:{self.id}:{self.subject[:40]}"


class TicketMessage(UUIDTimeStampedModel):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name="messages")
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="ticket_messages"
    )
    body = models.TextField()
    is_staff = models.BooleanField(default=False)
    attachment = models.FileField(upload_to="tickets/", null=True, blank=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"message:{self.ticket_id}"


class RewardDispute(UUIDTimeStampedModel):
    class Status(models.TextChoices):
        OPEN = "open", "Open"
        INVESTIGATING = "investigating", "Investigating"
        PROVIDER_CONTACTED = "provider_contacted", "Provider contacted"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"
        CLOSED = "closed", "Closed"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reward_disputes"
    )
    ticket = models.ForeignKey(
        Ticket, null=True, blank=True, on_delete=models.SET_NULL, related_name="disputes"
    )
    source = models.CharField(max_length=16, help_text="offer / survey / game")
    reference = models.CharField(max_length=191, blank=True)
    description = models.TextField(blank=True)
    screenshot = models.FileField(upload_to="disputes/", null=True, blank=True)

    status = models.CharField(
        max_length=24, choices=Status.choices, default=Status.OPEN, db_index=True
    )
    resolution_note = models.CharField(max_length=255, blank=True)
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="disputes_resolved",
    )
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"dispute:{self.id}:{self.status}"
