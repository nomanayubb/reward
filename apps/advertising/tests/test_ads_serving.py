"""Ad serving tests: placement selection, frequency caps, click tracking."""
import pytest
from django.contrib.auth import get_user_model
from django.test import Client

from apps.advertising.models import (
    AdCampaign,
    AdClick,
    AdImpression,
    AdPlacement,
    AdProvider,
)
from apps.advertising.services import record_impression, select_campaign, serve_ad
from apps.wallets.services import get_wallet

pytestmark = pytest.mark.django_db

STRONG_PASSWORD = "StrongPass123!"


@pytest.fixture
def user():
    account = get_user_model().objects.create_user(
        email="ads@example.com", password=STRONG_PASSWORD
    )
    get_wallet(account)
    return account


@pytest.fixture
def client():
    return Client()


@pytest.fixture
def provider():
    return AdProvider.objects.create(
        code="house", name="House", kind=AdProvider.Kind.HOUSE, is_enabled=True
    )


@pytest.fixture
def placement():
    return AdPlacement.objects.create(code="dashboard", name="Dashboard")


def _campaign(provider, placement, **overrides):
    defaults = {
        "provider": provider,
        "name": "House promo",
        "ad_type": AdCampaign.AdType.BANNER,
        "status": AdCampaign.Status.ACTIVE,
        "weight": 100,
    }
    defaults.update(overrides)
    campaign = AdCampaign.objects.create(**defaults)
    campaign.placements.add(placement)
    return campaign


def test_select_returns_none_without_placement(provider, user):
    campaign, placement = select_campaign("missing", user=user)

    assert campaign is None
    assert placement is None


def test_select_returns_active_campaign(provider, placement, user):
    campaign = _campaign(provider, placement)

    selected, _ = select_campaign("dashboard", user=user)

    assert selected == campaign


def test_disabled_provider_is_ignored(provider, placement, user):
    provider.is_enabled = False
    provider.save(update_fields=["is_enabled"])
    _campaign(provider, placement)

    assert select_campaign("dashboard", user=user)[0] is None


def test_frequency_cap_blocks_repeat(provider, placement, user):
    _campaign(provider, placement, max_per_day=1, max_per_hour=1, min_interval_minutes=0)

    selected, _ = select_campaign("dashboard", user=user)
    record_impression(campaign=selected, placement=placement, user=user)

    assert select_campaign("dashboard", user=user)[0] is None


def test_serve_ad_records_impression(provider, placement, user):
    campaign = _campaign(provider, placement)
    request = type("R", (), {"user": user, "META": {}})()

    slot = serve_ad("dashboard", request)

    assert slot.campaign == campaign
    assert AdImpression.objects.filter(campaign=campaign, user=user).count() == 1


def test_click_records_and_redirects(client, provider, placement, user):
    campaign = _campaign(provider, placement, target_url="https://example.com/landing")
    impression = record_impression(campaign=campaign, placement=placement, user=user)

    client.force_login(user)
    response = client.get(f"/ads/click/{impression.id}/")

    assert response.status_code == 302
    assert response.url == "https://example.com/landing"
    assert AdClick.objects.filter(impression=impression).count() == 1


def test_dashboard_renders_ad(client, provider, placement, user):
    _campaign(provider, placement)

    client.force_login(user)
    response = client.get("/")

    assert response.status_code == 200
    assert b"Sponsored" in response.content
