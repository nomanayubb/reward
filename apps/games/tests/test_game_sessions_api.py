"""Game session API tests (the Game SDK server side)."""
from datetime import timedelta
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient

from apps.games.models import Game, GameRewardRule, GameSession
from apps.rewards.models import Reward
from apps.wallets.services import get_wallet, points_account

pytestmark = pytest.mark.django_db

STRONG_PASSWORD = "StrongPass123!"


@pytest.fixture
def user():
    account = get_user_model().objects.create_user(
        email="gamer@example.com", password=STRONG_PASSWORD
    )
    get_wallet(account)
    return account


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def game():
    return Game.objects.create(
        slug="tapper",
        title="Tapper",
        entry_path="tapper/game.html",
        min_session_seconds=1,
    )


def _start(client, game):
    return client.post(f"/api/v1/games/{game.slug}/sessions/", {}, format="json")


def test_start_session_requires_authentication(client, game):
    assert _start(client, game).status_code in (401, 403)


def test_start_session_returns_token(client, user, game):
    client.force_login(user)
    response = _start(client, game)

    assert response.status_code == 201
    assert response.data["session_token"]
    assert response.data["status"] == GameSession.Status.ACTIVE
    assert response.data["game"] == "tapper"


def test_start_session_rejects_paused_game(client, user, game):
    game.status = Game.Status.PAUSED
    game.save(update_fields=["status"])

    client.force_login(user)
    assert _start(client, game).status_code == 404


def test_report_event(client, user, game):
    client.force_login(user)
    token = _start(client, game).data["session_token"]

    response = client.post(
        f"/api/v1/games/sessions/{token}/events/",
        {"type": "level_start", "payload": {"level": 1}},
        format="json",
    )

    assert response.status_code == 201
    assert GameSession.objects.get(session_token=token).events.count() == 1


def test_short_session_is_invalidated(client, user, game):
    client.force_login(user)
    token = _start(client, game).data["session_token"]

    response = client.post(
        f"/api/v1/games/sessions/{token}/end/", {"score": 5}, format="json"
    )

    assert response.status_code == 200
    assert response.data["status"] == GameSession.Status.INVALIDATED


def test_rewarded_session_pays_points(client, user, game):
    GameRewardRule.objects.create(
        game=game,
        name="Score 10",
        conditions={"min_score": 10},
        mode=GameRewardRule.Mode.POINTS,
        points=Decimal("10"),
        cooldown_hours=0,
        daily_max=5,
        monthly_max=50,
    )

    client.force_login(user)
    token = _start(client, game).data["session_token"]
    # Make the session long enough to pass server-side duration validation.
    GameSession.objects.filter(session_token=token).update(
        started_at=timezone.now() - timedelta(seconds=5)
    )

    response = client.post(
        f"/api/v1/games/sessions/{token}/end/", {"score": 15}, format="json"
    )

    assert response.data["status"] == GameSession.Status.ENDED
    assert Reward.objects.filter(user=user, source=Reward.Source.GAME).exists()
    assert points_account(user).balance == Decimal("10.00")


def test_cannot_end_another_users_session(client, user, game):
    other = get_user_model().objects.create_user(
        email="gamer-other@example.com", password=STRONG_PASSWORD
    )
    get_wallet(other)
    client.force_login(other)
    token = _start(client, game).data["session_token"]

    client.force_login(user)
    response = client.post(
        f"/api/v1/games/sessions/{token}/end/", {"score": 1}, format="json"
    )

    assert response.status_code == 404
