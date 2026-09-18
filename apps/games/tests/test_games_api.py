"""Game catalog API tests."""
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.games.models import Game, GameCategory
from apps.wallets.services import get_wallet

pytestmark = pytest.mark.django_db

GAMES_URL = "/api/v1/games/"
STRONG_PASSWORD = "StrongPass123!"


@pytest.fixture
def user():
    account = get_user_model().objects.create_user(
        email="games@example.com", password=STRONG_PASSWORD
    )
    get_wallet(account)
    return account


@pytest.fixture
def client():
    return APIClient()


def test_games_list_requires_authentication(client):
    assert client.get(GAMES_URL).status_code in (401, 403)


def test_games_list_returns_only_active_games(client, user):
    category = GameCategory.objects.create(name="Arcade", slug="arcade")
    Game.objects.create(
        slug="flappy", title="Flappy", entry_path="flappy/game.html", category=category
    )
    Game.objects.create(
        slug="hidden",
        title="Hidden",
        entry_path="hidden/game.html",
        status=Game.Status.PAUSED,
    )

    client.force_login(user)
    response = client.get(GAMES_URL)

    assert response.status_code == 200
    slugs = [row["slug"] for row in response.data["results"]]
    assert slugs == ["flappy"]
    assert response.data["results"][0]["category"] == "Arcade"
