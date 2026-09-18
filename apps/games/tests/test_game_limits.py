"""Game plays-remaining tests."""
import pytest
from django.contrib.auth import get_user_model
from django.test import Client

from apps.games.models import Game, GameSession
from apps.wallets.services import get_wallet

pytestmark = pytest.mark.django_db

STRONG_PASSWORD = "StrongPass123!"


@pytest.fixture
def user():
    account = get_user_model().objects.create_user(
        email="limits-game@example.com", password=STRONG_PASSWORD
    )
    get_wallet(account)
    return account


@pytest.fixture
def client():
    return Client()


@pytest.fixture
def game():
    return Game.objects.create(
        slug="limited-game",
        title="Limited Game",
        entry_path="game.html",
        max_daily_sessions=2,
    )


def test_games_page_shows_plays_left(client, user, game):
    GameSession.objects.create(user=user, game=game, session_token="t1")

    client.force_login(user)
    content = client.get("/games/").content.decode("utf-8")

    assert "1 of 2 plays left today" in content


def test_games_page_blocks_when_exhausted(client, user, game):
    GameSession.objects.create(user=user, game=game, session_token="t1")
    GameSession.objects.create(user=user, game=game, session_token="t2")

    client.force_login(user)
    content = client.get("/games/").content.decode("utf-8")

    assert "Come back tomorrow" in content
