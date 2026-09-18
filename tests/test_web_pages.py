"""Server-rendered page tests: auth, dashboard, earning and money pages."""
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.test import Client

from apps.cpa.models import CPAProvider
from apps.games.models import Game
from apps.notifications.models import Notification
from apps.offers.models import Offer
from apps.payments.models import PaymentProvider
from apps.rewards.models import Reward
from apps.rewards.services import RewardService
from apps.surveys.models import Survey, SurveyProvider
from apps.wallets.services import get_wallet
from apps.withdrawals.models import WithdrawalMethod

pytestmark = pytest.mark.django_db

STRONG_PASSWORD = "StrongPass123!"

PROTECTED_URLS = [
    "/",
    "/wallet/",
    "/transactions/",
    "/games/",
    "/offers/",
    "/surveys/",
    "/withdraw/",
    "/deposit/",
    "/alerts/",
]


@pytest.fixture
def user():
    account = get_user_model().objects.create_user(
        email="web@example.com", password=STRONG_PASSWORD
    )
    get_wallet(account)
    return account


@pytest.fixture
def client():
    return Client()


@pytest.mark.parametrize("url", PROTECTED_URLS)
def test_pages_require_login(client, url):
    response = client.get(url)
    assert response.status_code == 302
    assert "/accounts/login/" in response.url


def test_register_page_creates_and_logs_in(client):
    response = client.post(
        "/accounts/register/",
        {
            "email": "new-web@example.com",
            "password1": STRONG_PASSWORD,
            "password2": STRONG_PASSWORD,
        },
    )

    assert response.status_code == 302
    user = get_user_model().objects.get(email="new-web@example.com")
    assert user.wallet.accounts.exists()
    assert client.get("/").status_code == 200


def test_login_page(client, user):
    response = client.post(
        "/accounts/login/", {"username": "web@example.com", "password": STRONG_PASSWORD}
    )

    assert response.status_code == 302
    assert client.get("/").status_code == 200


def test_dashboard_shows_balance(client, user):
    RewardService.award_fixed(
        user=user, source=Reward.Source.PROMOTION, cash=Decimal("500"), source_reference="web-topup"
    )
    client.force_login(user)

    response = client.get("/")

    assert response.status_code == 200
    assert b"500" in response.content


def test_wallet_and_transactions_pages(client, user):
    RewardService.award_fixed(
        user=user, source=Reward.Source.PROMOTION, cash=Decimal("250"), source_reference="web-wallet"
    )
    client.force_login(user)

    assert b"250" in client.get("/wallet/").content
    assert b"250" in client.get("/transactions/").content


def test_games_page_lists_active_game(client, user):
    Game.objects.create(slug="tapper", title="Tapper", entry_path="game.html")
    client.force_login(user)

    assert b"Tapper" in client.get("/games/").content


def test_offers_page_shows_only_eligible(client, user):
    provider = CPAProvider.objects.create(
        code="web_net", name="WebNet", adapter_path="apps.cpa.providers.base.CPAProviderAdapter"
    )
    Offer.objects.create(
        provider=provider,
        external_id="ok",
        title="Good offer",
        payout=Decimal("2"),
        user_reward=Decimal("560"),
        incentive_allowed=True,
    )
    Offer.objects.create(
        provider=provider,
        external_id="no",
        title="Bad offer",
        payout=Decimal("2"),
        user_reward=Decimal("560"),
        incentive_allowed=False,
    )
    client.force_login(user)

    content = client.get("/offers/").content

    assert b"Good offer" in content
    assert b"Bad offer" not in content


def test_surveys_page(client, user):
    provider = SurveyProvider.objects.create(
        code="web_survey",
        name="WebSurvey",
        adapter_path="apps.surveys.providers.base.SurveyProviderAdapter",
    )
    Survey.objects.create(
        provider=provider,
        external_id="s1",
        title="Short survey",
        payout=Decimal("1"),
        user_reward=Decimal("280"),
    )
    client.force_login(user)

    assert b"Short survey" in client.get("/surveys/").content


def test_withdraw_page_add_method_and_request(client, user):
    RewardService.award_fixed(
        user=user,
        source=Reward.Source.PROMOTION,
        cash=Decimal("5000"),
        source_reference="web-withdraw",
    )
    client.force_login(user)

    response = client.post(
        "/withdraw/",
        {
            "action": "add_method",
            "type": "easypaisa",
            "label": "Mine",
            "account_number": "03001234567",
        },
    )
    assert response.status_code == 302
    method = WithdrawalMethod.objects.get(user=user)

    response = client.post("/withdraw/", {"method": str(method.id), "amount": "1000.00"})

    assert response.status_code == 302
    assert b"1000" in client.get("/withdraw/").content


def test_deposit_page_creates_payment(client, user):
    provider = PaymentProvider.objects.create(
        code="manual",
        name="Manual",
        kind=PaymentProvider.Kind.LOCAL,
        is_enabled=True,
        supports_deposits=True,
        config={"adapter_path": "apps.payments.providers.manual.ManualProviderAdapter"},
    )
    client.force_login(user)

    response = client.post("/deposit/", {"provider": provider.id, "amount": "1000.00"})

    assert response.status_code == 200
    assert b"Payment instructions" in response.content


def test_notifications_page(client, user):
    Notification.objects.create(user=user, title="Hello web")
    client.force_login(user)

    assert b"Hello web" in client.get("/alerts/").content
