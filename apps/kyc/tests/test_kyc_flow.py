"""KYC flow tests: submission and admin review."""
import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client

from apps.adminpanel.models import AuditLog
from apps.kyc.models import KYCVerification
from apps.wallets.services import get_wallet

pytestmark = pytest.mark.django_db

STRONG_PASSWORD = "StrongPass123!"


@pytest.fixture
def user():
    account = get_user_model().objects.create_user(
        email="kyc-user@example.com", password=STRONG_PASSWORD
    )
    get_wallet(account)
    return account


@pytest.fixture
def staff():
    account = get_user_model().objects.create_user(
        email="kyc-staff@example.com", password=STRONG_PASSWORD, is_staff=True
    )
    get_wallet(account)
    return account


@pytest.fixture
def client():
    return Client()


def test_kyc_page_requires_login(client):
    assert client.get("/kyc/").status_code == 302


def test_submit_basic_kyc(client, user):
    client.force_login(user)

    response = client.post("/kyc/", {"full_name": "Noman Ayub"})

    assert response.status_code == 302
    kyc = KYCVerification.objects.get(user=user)
    assert kyc.status == KYCVerification.Status.UNDER_REVIEW
    assert kyc.level == KYCVerification.Level.BASIC


def test_submit_full_kyc_with_document(client, user, settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path
    client.force_login(user)

    upload = SimpleUploadedFile("cnic.jpg", b"fake-image-bytes", content_type="image/jpeg")
    response = client.post(
        "/kyc/",
        {
            "full_name": "Noman Ayub",
            "document_type": "cnic",
            "document_number": "12345-6789012-3",
            "document_front": upload,
        },
    )

    assert response.status_code == 302
    kyc = KYCVerification.objects.get(user=user)
    assert kyc.level == KYCVerification.Level.FULL
    assert kyc.document_front


def test_cannot_resubmit_while_under_review(client, user):
    client.force_login(user)
    client.post("/kyc/", {"full_name": "First submission"})

    response = client.post("/kyc/", {"full_name": "Second submission"})

    assert response.status_code == 200
    kyc = KYCVerification.objects.get(user=user)
    assert kyc.full_name == "First submission"


def test_admin_queue_and_approve(client, staff, user):
    client.force_login(user)
    client.post("/kyc/", {"full_name": "Noman Ayub"})
    kyc = KYCVerification.objects.get(user=user)

    client.force_login(staff)
    queue = client.get("/admin-panel/kyc/")
    assert queue.status_code == 200
    assert b"kyc-user@example.com" in queue.content

    client.post(f"/admin-panel/kyc/{kyc.id}/action/", {"action": "approve"})

    kyc.refresh_from_db()
    assert kyc.status == KYCVerification.Status.APPROVED
    assert AuditLog.objects.filter(action="kyc.approve").exists()


def test_admin_reject_records_reason(client, staff, user):
    client.force_login(user)
    client.post("/kyc/", {"full_name": "Noman Ayub"})
    kyc = KYCVerification.objects.get(user=user)

    client.force_login(staff)
    client.post(
        f"/admin-panel/kyc/{kyc.id}/action/", {"action": "reject", "reason": "blurry document"}
    )

    kyc.refresh_from_db()
    assert kyc.status == KYCVerification.Status.REJECTED
    assert kyc.rejection_reason == "blurry document"


def test_admin_kyc_requires_staff(client, user):
    client.force_login(user)
    assert client.get("/admin-panel/kyc/").status_code == 403
