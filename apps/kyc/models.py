"""KYC verification.

Collect only what is genuinely required for payments/legal compliance.
KYC files are private — they must be stored on private object storage and
served only through permission-checked views.
"""
from django.conf import settings
from django.db import models

from apps.common.models import UUIDTimeStampedModel


class KYCVerification(UUIDTimeStampedModel):
    class Status(models.TextChoices):
        NOT_STARTED = "not_started", "Not started"
        PENDING = "pending", "Pending"
        UNDER_REVIEW = "under_review", "Under review"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"
        EXPIRED = "expired", "Expired"

    class Level(models.TextChoices):
        NONE = "none", "None"
        BASIC = "basic", "Basic (name + DOB)"
        FULL = "full", "Full (ID document + selfie)"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="kyc"
    )
    status = models.CharField(
        max_length=16, choices=Status.choices, default=Status.NOT_STARTED, db_index=True
    )
    level = models.CharField(max_length=16, choices=Level.choices, default=Level.NONE)

    full_name = models.CharField(max_length=160, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    country = models.CharField(max_length=2, blank=True)
    address = models.CharField(max_length=255, blank=True)

    document_type = models.CharField(max_length=32, blank=True)
    document_number = models.CharField(max_length=64, blank=True)
    document_front = models.FileField(upload_to="kyc/", null=True, blank=True)
    document_back = models.FileField(upload_to="kyc/", null=True, blank=True)
    selfie = models.FileField(upload_to="kyc/", null=True, blank=True)

    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="kyc_reviewed",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.CharField(max_length=255, blank=True)
    provider_reference = models.CharField(max_length=191, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"kyc:{self.user_id}:{self.status}"
