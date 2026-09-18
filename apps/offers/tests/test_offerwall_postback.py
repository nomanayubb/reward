"""Offerwall postback tests: conversions without a click, resolved by player id."""
import hashlib
import hmac
import json
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.test import override_settings

from apps.accounts.services import player_id_for
from apps.cpa.models import CPAProvider
from apps.offers.models import Offer, OfferConversion
from apps.offers.services import process_postback
from apps.rewards.models import Reward, RewardRule
from apps.wallets.models import WalletAccount
from apps.wallets.services import get_account, get_wallet

pytestmark = pytest.mark.django_db

POSTBACK_KEY = "test-postback-key"


@pytest.fixture
def user():
    account = get_user_model().objects.create_user(
        email="offerwall@example.com", password="StrongPass123!"
    )
    get_wallet(account)
    return account


@pytest.fixture
def provider():
    return CPAProvider.objects.create(
        code="adgem",
        name="AdGem",
        adapter_path="apps.cpa.providers.adgem.AdgemAdapter",
        is_enabled=True,
        config={"incentive_allowed": True},
    )


@pytest.fixture
def rule():
    return RewardRule.objects.create(
        name="Offer 40%",
        source=RewardRule.Source.OFFER,
        user_percentage=Decimal("40"),
        reward_currency="USD",
    )


def _payload(user, **overrides):
    data = {
        "conversion_id": "conv-1",
        "player_id": player_id_for(user),
        "payout": 2.0,
        "offer_id": "offer-99",
        "offer_name": "Install App X",
        "conversion_type": "reward",
        "country": "PK",
    }
    data.update(overrides)
    return {"request_id": "req-1", "timestamp": 1, "data": data}


def _postback(provider, payload):
    body = json.dumps(payload).encode("utf-8")
    signature = hmac.new(POSTBACK_KEY.encode(), body, hashlib.sha256).hexdigest()
    return process_postback(
        provider, payload, headers={"Signature": signature}, ip="1.2.3.4", raw_body=body
    )


@override_settings(ADGEM_POSTBACK_KEY=POSTBACK_KEY)
def test_offerwall_postback_creates_offer_and_pays(provider, user, rule):
    payload = _payload(user)

    conversion, created = _postback(provider, payload)

    assert created is True
    assert conversion.status == OfferConversion.Status.APPROVED
    assert conversion.user == user

    offer = Offer.objects.get(provider=provider, external_id="offer-99")
    assert offer.title == "Install App X"
    assert offer.incentive_allowed is True

    reward = Reward.objects.get(user=user, source=Reward.Source.OFFER)
    assert reward.user_reward == Decimal("0.80")  # 40% of $2
    assert get_account(user, WalletAccount.Type.CASH, "USD").balance == Decimal("0.80")


@override_settings(ADGEM_POSTBACK_KEY=POSTBACK_KEY)
def test_offerwall_postback_is_idempotent(provider, user, rule):
    payload = _payload(user)

    first, created_first = _postback(provider, payload)
    second, created_second = _postback(provider, payload)

    assert created_first is True
    assert created_second is False
    assert first.pk == second.pk
    assert OfferConversion.objects.filter(provider=provider).count() == 1


@override_settings(ADGEM_POSTBACK_KEY=POSTBACK_KEY)
def test_offerwall_postback_respects_incentive_compliance(provider, user, rule):
    provider.config = {"incentive_allowed": False}
    provider.save(update_fields=["config"])
    payload = _payload(user, conversion_id="conv-2")

    conversion, created = _postback(provider, payload)

    assert created is True
    assert conversion.status == OfferConversion.Status.REJECTED
    assert conversion.offer.external_id == "offer-99"
    assert not Reward.objects.filter(user=user).exists()
    assert get_account(user, WalletAccount.Type.CASH, "USD").balance == Decimal("0")


@override_settings(ADGEM_POSTBACK_KEY=POSTBACK_KEY)
def test_unknown_player_id_is_rejected(provider, user, rule):
    payload = _payload(user, player_id="not-our-format")

    conversion, created = _postback(provider, payload)

    assert conversion is None
    assert created is False
    assert OfferConversion.objects.count() == 0
