"""Direct-ads admin UI tests."""
import pytest
from django.contrib.auth import get_user_model
from django.test import Client

from apps.adminpanel.models import AuditLog
from apps.advertising.models import AdCampaign, AdPlacement, AdProvider
from apps.wallets.services import get_wallet

pytestmark = pytest.mark.django_db

STRONG_PASSWORD = "StrongPass123!"


@pytest.fixture
def staff():
    account = get_user_model().objects.create_user(
        email="ads-staff@example.com", password=STRONG_PASSWORD, is_staff=True
    )
    get_wallet(account)
    return account


@pytest.fixture
def player():
    account = get_user_model().objects.create_user(
        email="ads-player@example.com", password=STRONG_PASSWORD
    )
    get_wallet(account)
    return account


@pytest.fixture
def client():
    return Client()


@pytest.fixture
def provider():
    return AdProvider.objects.create(
        code="direct_house", name="Direct House", kind=AdProvider.Kind.DIRECT, is_enabled=True
    )


@pytest.fixture
def placement():
    return AdPlacement.objects.create(code="dashboard", name="Dashboard")


def test_ads_page_requires_staff(client, player):
    client.force_login(player)
    assert client.get("/admin-panel/ads/").status_code == 403


def test_create_campaign_via_admin(client, staff, provider, placement):
    client.force_login(staff)

    response = client.post(
        "/admin-panel/ads/",
        {
            "name": "Eid promo",
            "provider": provider.id,
            "ad_type": AdCampaign.AdType.BANNER,
            "target_url": "https://advertiser.example/eid",
            "placements": [placement.id],
            "weight": 150,
            "max_per_hour": 3,
            "min_interval_minutes": 10,
            "max_per_day": 10,
        },
    )

    assert response.status_code == 302
    campaign = AdCampaign.objects.get(name="Eid promo")
    assert campaign.status == AdCampaign.Status.ACTIVE
    assert list(campaign.placements.all()) == [placement]
    assert AuditLog.objects.filter(action="ad_campaign.create").exists()


def test_created_campaign_is_served(client, staff, player, provider, placement):
    campaign = AdCampaign.objects.create(
        provider=provider,
        name="House banner",
        ad_type=AdCampaign.AdType.BANNER,
        status=AdCampaign.Status.ACTIVE,
        target_url="https://advertiser.example/promo",
    )
    campaign.placements.add(placement)

    client.force_login(player)
    content = client.get("/").content.decode("utf-8")

    assert "House banner" in content
    assert "Sponsored" in content


def test_toggle_campaign(client, staff, provider, placement):
    campaign = AdCampaign.objects.create(
        provider=provider,
        name="Toggle me",
        ad_type=AdCampaign.AdType.NATIVE,
        status=AdCampaign.Status.ACTIVE,
    )
    campaign.placements.add(placement)
    client.force_login(staff)

    client.post(f"/admin-panel/ads/{campaign.id}/action/")

    campaign.refresh_from_db()
    assert campaign.status == AdCampaign.Status.PAUSED
    assert AuditLog.objects.filter(action="ad_campaign.toggle").exists()
