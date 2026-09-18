"""Survey catalog API tests."""
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.surveys.models import Survey, SurveyProvider
from apps.wallets.services import get_wallet

pytestmark = pytest.mark.django_db

SURVEYS_URL = "/api/v1/surveys/"
STRONG_PASSWORD = "StrongPass123!"


@pytest.fixture
def user():
    account = get_user_model().objects.create_user(
        email="surveys@example.com", password=STRONG_PASSWORD
    )
    get_wallet(account)
    return account


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def provider():
    return SurveyProvider.objects.create(
        code="survey_a",
        name="Survey A",
        adapter_path="apps.surveys.providers.base.SurveyProviderAdapter",
    )


def test_surveys_list_requires_authentication(client):
    assert client.get(SURVEYS_URL).status_code in (401, 403)


def test_surveys_list_returns_active_surveys_only(client, user, provider):
    Survey.objects.create(
        provider=provider,
        external_id="s1",
        title="Active survey",
        payout=Decimal("1.00"),
        user_reward=Decimal("224.00"),
    )
    Survey.objects.create(
        provider=provider,
        external_id="s2",
        title="Paused survey",
        payout=Decimal("1.00"),
        user_reward=Decimal("224.00"),
        status=Survey.Status.PAUSED,
    )

    client.force_login(user)
    response = client.get(SURVEYS_URL)

    assert response.status_code == 200
    titles = [row["title"] for row in response.data["results"]]
    assert titles == ["Active survey"]
    assert response.data["results"][0]["provider"] == "Survey A"
