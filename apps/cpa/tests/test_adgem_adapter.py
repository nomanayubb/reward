"""AdGem adapter tests (Offer API parsing, click tagging, v3 signatures)."""
import hashlib
import hmac
import json
from decimal import Decimal

import pytest
from django.test import override_settings

from apps.cpa.models import CPAProvider
from apps.cpa.providers.adgem import AdgemAdapter

pytestmark = pytest.mark.django_db


@pytest.fixture
def provider():
    return CPAProvider.objects.create(
        code="adgem",
        name="AdGem",
        adapter_path="apps.cpa.providers.adgem.AdgemAdapter",
        is_enabled=False,
        config={"api_base": "https://offer-api.adgem.com", "incentive_allowed": True},
    )


@pytest.fixture
def adapter(provider):
    return AdgemAdapter(provider)


SAMPLE_OFFER = {
    "id": "1234567894561234567",
    "campaign_id": 1,
    "name": "Offer Name",
    "store_id": "com.adgem.app",
    "tracking_type": "CPI",
    "total_payout_usd": 1.25,
    "total_amount": 5,
    "is_multi_reward": True,
    "campaign_vertical": "Content Discovery",
    "creatives": {
        "name": "Offer Name",
        "icon_url": "https://adgem.com/images/icon.png",
        "description": "Offer Description",
        "instructions": ["Install the app", "Reach level 5"],
        "categories": ["app"],
    },
    "links": {
        "click_url": "https://api.adgem.com/v1/click?all=1&appid=1&cid=100&playerid={playerid}",
    },
    "geo_targeting": {"countries": [{"name": "Pakistan", "iso_alpha2": "PK"}]},
    "device_targeting": ["android_phone"],
    "os_targeting": [{"name": "android", "min": "8.0", "max": ""}],
}


def test_get_offers_normalizes_fields(adapter, monkeypatch):
    monkeypatch.setattr(adapter, "_request", lambda path, params=None: {"data": [SAMPLE_OFFER]})

    offers = adapter.get_offers()

    assert len(offers) == 1
    offer = offers[0]
    assert offer.external_id == "1234567894561234567"
    assert offer.title == "Offer Name"
    assert offer.payout == Decimal("1.25")
    assert offer.countries == ["PK"]
    assert offer.devices == ["android_phone"]
    assert offer.operating_systems == ["android"]
    assert offer.incentive_allowed is True
    assert offer.multiple_completion_allowed is True
    assert "Install the app" in offer.description


def test_incentive_flag_defaults_to_false(provider, monkeypatch):
    provider.config = {"api_base": "https://offer-api.adgem.com"}
    provider.save(update_fields=["config"])
    adapter = AdgemAdapter(provider)
    monkeypatch.setattr(adapter, "_request", lambda path, params=None: {"data": [SAMPLE_OFFER]})

    assert adapter.get_offers()[0].incentive_allowed is False


def test_track_click_replaces_player_placeholder(adapter):
    class Offer:
        tracking_url = "https://api.adgem.com/v1/click?cid=100&playerid={playerid}"

    url = adapter.track_click(Offer(), None, "click-abc")

    assert url.endswith("playerid=click-abc")


@override_settings(ADGEM_REFRESH_TOKEN="refresh-123")
def test_access_token_is_exchanged_and_cached(adapter, monkeypatch):
    calls = {"count": 0}

    def fake_exchange():
        calls["count"] += 1
        return "access-abc", 3600

    monkeypatch.setattr(adapter, "_exchange_token", fake_exchange)

    assert adapter._get_access_token() == "access-abc"
    assert adapter._get_access_token() == "access-abc"
    assert calls["count"] == 1  # second call served from cache


@override_settings(ADGEM_REFRESH_TOKEN="", ADGEM_API_KEY="")
def test_missing_refresh_token_raises(adapter):
    from apps.cpa.providers.base import ProviderConfigurationError

    with pytest.raises(ProviderConfigurationError):
        adapter._exchange_token()


def _sign(body: bytes, key: str) -> str:
    return hmac.new(key.encode(), body, hashlib.sha256).hexdigest()


@override_settings(ADGEM_POSTBACK_KEY="postback-secret")
def test_validate_signature_accepts_valid(adapter):
    body = json.dumps({"request_id": "1", "timestamp": 1, "data": {}}).encode()

    assert adapter.validate_signature({}, {"Signature": _sign(body, "postback-secret")}, body) is True


@override_settings(ADGEM_POSTBACK_KEY="postback-secret")
def test_validate_signature_rejects_tampered_body(adapter):
    body = b'{"request_id":"1"}'
    tampered = b'{"request_id":"2"}'

    assert adapter.validate_signature({}, {"Signature": _sign(body, "postback-secret")}, tampered) is False


@override_settings(ADGEM_POSTBACK_KEY="")
def test_validate_signature_without_key(adapter):
    assert adapter.validate_signature({}, {"Signature": "whatever"}, b"{}") is False


def test_process_postback_reward_is_approved(adapter):
    payload = {
        "request_id": "r1",
        "timestamp": 1,
        "data": {
            "conversion_id": "c1",
            "player_id": "click-1",
            "payout": 1.5,
            "offer_id": "o1",
            "conversion_type": "reward",
        },
    }

    conversion = adapter.process_postback(payload)

    assert conversion.external_conversion_id == "c1"
    assert conversion.user_identifier == "click-1"
    assert conversion.payout == Decimal("1.5")
    assert conversion.status == "approved"


def test_process_postback_install_is_rejected(adapter):
    payload = {
        "data": {
            "conversion_id": "c2",
            "player_id": "click-2",
            "payout": 0,
            "conversion_type": "install",
        }
    }

    conversion = adapter.process_postback(payload)

    assert conversion.status == "rejected"
    assert "install" in conversion.reason
