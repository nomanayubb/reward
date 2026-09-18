"""Public pages tests: landing page and CMS static pages."""
import pytest
from django.contrib.auth import get_user_model
from django.test import Client

from apps.cms.models import CMSPage
from apps.wallets.services import get_wallet

pytestmark = pytest.mark.django_db

STRONG_PASSWORD = "StrongPass123!"


@pytest.fixture
def user():
    account = get_user_model().objects.create_user(
        email="public@example.com", password=STRONG_PASSWORD
    )
    get_wallet(account)
    return account


@pytest.fixture
def client():
    return Client()


@pytest.fixture
def terms_page():
    return CMSPage.objects.create(
        slug="terms",
        title="Terms of Service",
        content="<p>Terms body</p>",
        status=CMSPage.Status.PUBLISHED,
    )


def test_landing_page_is_public(client):
    response = client.get("/")

    assert response.status_code == 200
    assert b"How it works" in response.content
    assert b"Create free account" in response.content


def test_landing_redirects_authenticated_users(client, user):
    client.force_login(user)

    response = client.get("/")

    assert response.status_code == 302
    assert response.url == "/dashboard/"


def test_cms_page_renders(client, terms_page):
    response = client.get("/p/terms/")

    assert response.status_code == 200
    assert b"Terms of Service" in response.content
    assert b"Terms body" in response.content


def test_unknown_cms_page_404(client):
    assert client.get("/p/does-not-exist/").status_code == 404


def test_draft_cms_page_is_not_public(client):
    CMSPage.objects.create(
        slug="draft-page",
        title="Draft",
        content="<p>hidden</p>",
        status=CMSPage.Status.DRAFT,
    )

    assert client.get("/p/draft-page/").status_code == 404


def test_footer_links_render_on_login_page(client):
    response = client.get("/accounts/login/")

    assert b"/p/about/" in response.content
    assert b"/p/terms/" in response.content
    assert b"/p/privacy/" in response.content
    assert b"/p/contact/" in response.content
