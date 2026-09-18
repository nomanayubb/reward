"""Global pytest fixtures.

The locmem cache is not rolled back with the database, so tests that write
cached settings (e.g. PlatformSetting via ``set_setting``) would leak state
into other tests. Clear the cache around every test.
"""
import pytest
from django.core.cache import cache


@pytest.fixture(autouse=True)
def _clear_cache_between_tests():
    cache.clear()
    yield
    cache.clear()
