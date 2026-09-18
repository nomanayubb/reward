"""SEO tests: robots.txt, sitemap.xml and per-path metadata."""
import pytest
from django.test import Client

from apps.cms.models import CMSPage
from apps.seo.models import SEOConfig

pytestmark = pytest.mark.django_db


@pytest.fixture
def client():
    return Client()


def test_robots_txt(client):
    response = client.get("/robots.txt")

    assert response.status_code == 200
    content = response.content.decode("utf-8")
    assert "Disallow: /admin/" in content
    assert "Disallow: /api/" in content
    assert "Sitemap:" in content
    assert "/sitemap.xml" in content


def test_sitemap_lists_public_pages(client):
    CMSPage.objects.create(
        slug="terms",
        title="Terms",
        content="<p>terms</p>",
        status=CMSPage.Status.PUBLISHED,
    )

    response = client.get("/sitemap.xml")

    assert response.status_code == 200
    content = response.content.decode("utf-8")
    assert "<urlset" in content
    assert "/p/terms/" in content


def test_draft_cms_page_is_not_in_sitemap(client):
    CMSPage.objects.create(
        slug="hidden", title="Hidden", content="x", status=CMSPage.Status.DRAFT
    )

    content = client.get("/sitemap.xml").content.decode("utf-8")

    assert "/p/hidden/" not in content


def test_seo_config_overrides_meta(client):
    SEOConfig.objects.create(
        path="/",
        title="Earn rewards in Pakistan",
        meta_description="Custom description here",
        robots="index,follow",
    )

    content = client.get("/").content.decode("utf-8")

    assert "Custom description here" in content
    assert "Earn rewards in Pakistan" in content


def test_default_meta_description_renders(client):
    content = client.get("/accounts/login/").content.decode("utf-8")

    assert "Earn rewards for games" in content
