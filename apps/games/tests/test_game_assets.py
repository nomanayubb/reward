"""Game player page and asset-serving tests."""
import pytest
from django.contrib.auth import get_user_model
from django.test import Client

from apps.games.models import Game
from apps.wallets.services import get_wallet

pytestmark = pytest.mark.django_db

STRONG_PASSWORD = "StrongPass123!"


@pytest.fixture
def user():
    account = get_user_model().objects.create_user(
        email="player@example.com", password=STRONG_PASSWORD
    )
    get_wallet(account)
    return account


@pytest.fixture
def client():
    return Client()


def test_player_page_requires_login(client):
    response = client.get("/play/tap-target/")
    assert response.status_code == 302


def test_player_page_renders_with_host_script(client, user):
    Game.objects.create(slug="tap-target", title="Tap Target", entry_path="game.html")

    client.force_login(user)
    response = client.get("/play/tap-target/")

    assert response.status_code == 200
    assert b"game-host.js" in response.content
    assert b"game-frame" in response.content


def test_player_page_404_for_paused_game(client, user):
    Game.objects.create(
        slug="paused-game",
        title="Paused",
        entry_path="game.html",
        status=Game.Status.PAUSED,
    )

    client.force_login(user)
    assert client.get("/play/paused-game/").status_code == 404


def test_asset_view_serves_game_files(client, settings, tmp_path):
    settings.GAMES_ROOT = tmp_path
    game_dir = tmp_path / "demo"
    game_dir.mkdir()
    (game_dir / "game.html").write_text("<html>demo</html>", encoding="utf-8")

    response = client.get("/games/demo/game.html")

    assert response.status_code == 200
    assert b"demo" in b"".join(response.streaming_content)


def test_asset_view_blocks_path_traversal(client, settings, tmp_path):
    settings.GAMES_ROOT = tmp_path
    (tmp_path / "demo").mkdir()
    (tmp_path / "secret.txt").write_text("secret", encoding="utf-8")

    response = client.get("/games/demo/../secret.txt")

    assert response.status_code == 404


def test_asset_view_unknown_game(client, settings, tmp_path):
    settings.GAMES_ROOT = tmp_path
    assert client.get("/games/nope/game.html").status_code == 404


def test_first_game_package_exists():
    """The bundled games ship with the required documentation."""
    from django.conf import settings as django_settings

    for slug in ("tap-target", "memory-match", "snake"):
        game_dir = django_settings.GAMES_ROOT / slug
        assert (game_dir / "game.html").is_file(), f"{slug} game.html missing"
        for doc in ("README.md", "API.md", "REWARD_RULES.md", "DEVELOPMENT.md"):
            assert (game_dir / "documentation" / doc).is_file(), f"{slug}/{doc} missing"
