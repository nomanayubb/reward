"""Survey start tests."""
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.test import Client

from apps.surveys.models import Survey, SurveyProvider, SurveySession
from apps.wallets.services import get_wallet

pytestmark = pytest.mark.django_db

STRONG_PASSWORD = "StrongPass123!"


@pytest.fixture
def user():
    account = get_user_model().objects.create_user(
        email="survey-start@example.com", password=STRONG_PASSWORD
    )
    get_wallet(account)
    return account


@pytest.fixture
def client():
    return Client()


@pytest.fixture
def provider():
    return SurveyProvider.objects.create(
        code="survey_start",
        name="Survey Start",
        adapter_path="apps.surveys.providers.base.SurveyProviderAdapter",
    )


def _survey(provider):
    return Survey.objects.create(
        provider=provider,
        external_id="s-start",
        title="Startable survey",
        payout=Decimal("1"),
        user_reward=Decimal("280"),
    )


def test_start_without_adapter_reports_error(client, user, provider):
    survey = _survey(provider)
    client.force_login(user)

    response = client.get(f"/surveys/{survey.id}/start/")

    assert response.status_code == 302
    assert response.url == "/surveys/"
    assert SurveySession.objects.filter(user=user, survey=survey).count() == 1


def test_start_redirects_to_provider_url(client, user, provider, monkeypatch):
    survey = _survey(provider)
    monkeypatch.setattr(
        "apps.surveys.views.survey_url",
        lambda survey_obj, user_obj, session: "https://surveys.example/start/1",
    )
    client.force_login(user)

    response = client.get(f"/surveys/{survey.id}/start/")

    assert response.status_code == 302
    assert response.url == "https://surveys.example/start/1"
    assert SurveySession.objects.filter(user=user, survey=survey).count() == 1
