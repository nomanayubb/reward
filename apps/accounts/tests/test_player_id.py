"""Player-id round-trip tests (AdGem-compatible stable ids)."""
import pytest
from django.contrib.auth import get_user_model

from apps.accounts.services import player_id_for, user_for_player_id
from apps.wallets.services import get_wallet

pytestmark = pytest.mark.django_db


@pytest.fixture
def user():
    account = get_user_model().objects.create_user(
        email="player-id@example.com", password="StrongPass123!"
    )
    get_wallet(account)
    return account


def test_player_id_is_stable_and_well_formed(user):
    value = player_id_for(user)

    assert value == player_id_for(user)  # constant per user
    assert value.startswith("u")
    assert len(value) == 33
    assert value.islower()
    assert value.isalnum()


def test_player_id_reverses_to_user(user):
    assert user_for_player_id(player_id_for(user)) == user


def test_foreign_player_ids_return_none():
    assert user_for_player_id("") is None
    assert user_for_player_id("someone-else") is None
    assert user_for_player_id("uZZZ") is None
