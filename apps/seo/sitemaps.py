"""Sitemaps for the public, indexable pages."""
from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from apps.cms.models import CMSPage


class StaticViewSitemap(Sitemap):
    priority = 1.0
    changefreq = "weekly"

    def items(self):
        return ["public-home"]

    def location(self, item):
        return reverse(item)


class CMSPageSitemap(Sitemap):
    priority = 0.5
    changefreq = "monthly"

    def items(self):
        return CMSPage.objects.filter(status=CMSPage.Status.PUBLISHED).order_by("slug")

    def lastmod(self, obj):
        return obj.updated_at

    def location(self, obj):
        return reverse("cms-page", args=[obj.slug])
