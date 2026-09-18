"""Earn hub tabs and offer rules visibility tests."""
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.test import Client

from apps.cpa.models import CPAProvider
from apps.games.models import Game
from apps.offers.models import Offer
from apps.surveys.models import Survey, SurveyProvider
from apps.wallets.services import get_wallet

pytestmark = pytest.mark.django_db

STRONG_PASSWORD = "StrongPass123!"


@pytest.fixture
def user():
    account = get_user_model().objects.create_user(
        email="earn-hub@example.com", password=STRONG_PASSWORD
    )
    get_wallet(account)
    return account


@pytest.fixture
def client():
    return Client()


@pytest.fixture
def provider():
    return CPAProvider.objects.create(
        code="hub_net",
        name="Hub Net",
        adapter_path="apps.cpa.providers.base.CPAProviderAdapter",
        is_enabled=True,
    )


@pytest.fixture
def offer(provider):
    return Offer.objects.create(
        provider=provider,
        external_id="hub-offer",
        title="Hub offer",
        payout=Decimal("2"),
        user_reward=Decimal("560"),
        incentive_allowed=True,
        countries=["PK"],
        devices=["android"],
        daily_user_limit=2,
        lifetime_user_limit=3,
    )


def test_earn_hub_requires_login(client):
    assert client.get("/earn/").status_code == 302


def test_offers_tab_shows_rules(client, user, offer):
    client.force_login(user)

    content = client.get("/earn/", {"tab": "offers"}).content.decode("utf-8")

    assert "Incentivized traffic allowed" in content
    assert "Countries: PK" in content
    assert "Your remaining: <strong>2</strong> today" in content
    assert "one per user" in content  # multiple completions not allowed


def test_games_tab_shows_plays_left(client, user):
    Game.objects.create(
        slug="hub-game", title="Hub Game", entry_path="game.html", max_daily_sessions=3
    )
    client.force_login(user)

    content = client.get("/earn/", {"tab": "games"}).content.decode("utf-8")

    assert "3 of 3 plays left today" in content


def test_surveys_tab_shows_surveys(client, user):
    provider = SurveyProvider.objects.create(
        code="hub_survey",
        name="HubSurvey",
        adapter_path="apps.surveys.providers.base.SurveyProviderAdapter",
    )
    Survey.objects.create(
        provider=provider,
        external_id="s1",
        title="Hub survey",
        payout=Decimal("1"),
        user_reward=Decimal("280"),
    )
    client.force_login(user)

    content = client.get("/earn/", {"tab": "surveys"}).content.decode("utf-8")

    assert "Hub survey" in content


def test_offer_detail_shows_rules_and_start(client, user, offer):
    client.force_login(user)

    content = client.get(f"/offers/{offer.id}/").content.decode("utf-8")

    assert "Incentivized traffic allowed" in content
    assert f"/offers/{offer.id}/start/" in content


def test_offer_detail_blocks_ineligible_offer(client, user, provider):
    blocked = Offer.objects.create(
        provider=provider,
        external_id="blocked",
        title="Blocked offer",
        payout=Decimal("2"),
        user_reward=Decimal("560"),
        incentive_allowed=False,
    )
    client.force_login(user)

    content = client.get(f"/offers/{blocked.id}/").content.decode("utf-8")

    assert "not available for your account" in content
