"""SEO views: robots.txt."""
from django.http import HttpResponse


def robots_txt(request):
    """Public crawlers: allow marketing pages, keep app/admin out of the index."""
    lines = [
        "User-agent: *",
        "Allow: /$",
        "Allow: /p/",
        "Disallow: /admin/",
        "Disallow: /admin-panel/",
        "Disallow: /api/",
        "Disallow: /accounts/",
        "Disallow: /dashboard/",
        "Disallow: /earn/",
        "Disallow: /wallet/",
        "Disallow: /transactions/",
        "Disallow: /deposit/",
        "Disallow: /withdraw/",
        "Disallow: /alerts/",
        "Disallow: /kyc/",
        "Disallow: /games/",
        "Disallow: /play/",
        "Disallow: /offers/",
        "Disallow: /surveys/",
        "Disallow: /ads/",
        "",
        f"Sitemap: {request.build_absolute_uri('/sitemap.xml')}",
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain")
