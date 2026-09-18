"""KYC services: submission and review.

Collect only what is required for payments/legal compliance; documents are
private files and are only served through permission-checked views.
"""
from django.db import transaction
from django.utils import timezone

from .models import KYCVerification


class KYCError(Exception):
    """Raised when a KYC submission or transition is not allowed."""


@transaction.atomic
def submit_verification(
    user,
    *,
    full_name: str,
    date_of_birth=None,
    country: str = "",
    address: str = "",
    document_type: str = "",
    document_number: str = "",
    document_front=None,
    document_back=None,
    selfie=None,
) -> KYCVerification:
    kyc, _ = KYCVerification.objects.get_or_create(user=user)

    if kyc.status == KYCVerification.Status.APPROVED:
        raise KYCError("Your identity is already verified.")
    if kyc.status == KYCVerification.Status.UNDER_REVIEW:
        raise KYCError("Your submission is already under review.")

    kyc.full_name = full_name
    kyc.date_of_birth = date_of_birth
    kyc.country = country or getattr(user, "country", "")
    kyc.address = address
    kyc.document_type = document_type
    kyc.document_number = document_number
    if document_front:
        kyc.document_front = document_front
    if document_back:
        kyc.document_back = document_back
    if selfie:
        kyc.selfie = selfie

    has_document = bool(kyc.document_front)
    kyc.level = KYCVerification.Level.FULL if has_document else KYCVerification.Level.BASIC
    kyc.status = KYCVerification.Status.UNDER_REVIEW
    kyc.rejection_reason = ""
    kyc.save()
    return kyc


@transaction.atomic
def approve_verification(kyc: KYCVerification, *, reviewer=None) -> KYCVerification:
    kyc.status = KYCVerification.Status.APPROVED
    kyc.reviewed_by = reviewer
    kyc.reviewed_at = timezone.now()
    kyc.rejection_reason = ""
    kyc.save()
    return kyc


@transaction.atomic
def reject_verification(
    kyc: KYCVerification, *, reviewer=None, reason: str = ""
) -> KYCVerification:
    kyc.status = KYCVerification.Status.REJECTED
    kyc.reviewed_by = reviewer
    kyc.reviewed_at = timezone.now()
    kyc.rejection_reason = reason[:255]
    kyc.save()
    return kyc


def is_verified(user) -> bool:
    return KYCVerification.objects.filter(
        user=user, status=KYCVerification.Status.APPROVED
    ).exists()
