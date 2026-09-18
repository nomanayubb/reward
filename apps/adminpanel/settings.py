"""Runtime platform settings.

Business configuration (points conversion, limits, fees, reward defaults)
lives in the database so admins can change it without deploys. Values fall
back to ``settings.PLATFORM_DEFAULTS``.
"""
from django.conf import settings as django_settings
from django.core.cache import cache

from .models import ConfigurationVersion, PlatformSetting

CACHE_PREFIX = "platform_setting:"
CACHE_TTL = 300
_MISSING = object()


def get_setting(key: str, default=None):
    cache_key = f"{CACHE_PREFIX}{key}"
    cached = cache.get(cache_key, _MISSING)
    if cached is not _MISSING:
        return cached

    try:
        value = PlatformSetting.objects.get(key=key).value
    except PlatformSetting.DoesNotExist:
        value = django_settings.PLATFORM_DEFAULTS.get(key, default)

    cache.set(cache_key, value, CACHE_TTL)
    return value


def set_setting(
    key: str,
    value,
    *,
    updated_by=None,
    group: str = "general",
    description: str = "",
    note: str = "",
) -> PlatformSetting:
    obj, _ = PlatformSetting.objects.get_or_create(
        key=key, defaults={"group": group, "description": description}
    )
    old_value = obj.value
    obj.value = value
    obj.updated_by = updated_by
    if description:
        obj.description = description
    obj.save(update_fields=["value", "updated_by", "description", "updated_at"])

    ConfigurationVersion.objects.create(
        key=key, old_value=old_value, new_value=value, changed_by=updated_by, note=note
    )
    cache.delete(f"{CACHE_PREFIX}{key}")
    return obj


def points_per_usd():
    return get_setting("POINTS_PER_USD", 100)


def usd_to_points(amount) -> int:
    from decimal import Decimal, ROUND_DOWN

    rate = Decimal(str(points_per_usd()))
    points = (Decimal(str(amount)) * rate).quantize(Decimal("1"), rounding=ROUND_DOWN)
    return int(points)
