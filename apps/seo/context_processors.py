"""Per-path SEO metadata from ``SEOConfig`` with safe defaults.

Admin-editable in /admin/ → SEO configurations. Cached briefly per path.
"""
from django.core.cache import cache

from .models import SEOConfig

CACHE_TTL = 300


def seo(request):
    cache_key = f"seo:{request.path}"
    data = cache.get(cache_key)
    if data is None:
        config = SEOConfig.objects.filter(path=request.path, is_active=True).first()
        data = (
            {
                "title": config.title,
                "description": config.meta_description,
                "canonical": config.canonical_url,
                "robots": config.robots,
                "og_title": config.og_title,
                "og_description": config.og_description,
                "og_image": config.og_image,
            }
            if config is not None
            else {}
        )
        cache.set(cache_key, data, CACHE_TTL)
    return {"seo": data}
