"""Test settings — fast hashing, in-memory cache, eager celery."""
from .base import *  # noqa: F401,F403

DEBUG = False
ALLOWED_HOSTS = ["*"]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
        "ATOMIC_REQUESTS": False,
    }
}

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}

PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.InMemoryStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}

# Throttling is disabled in tests so repeated auth calls never flake.
REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"] = dict.fromkeys(  # noqa: F405
    REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"], None  # noqa: F405
)

# Static-file serving middleware is irrelevant in tests (and warns when
# staticfiles/ has not been collected).
MIDDLEWARE = [m for m in MIDDLEWARE if "whitenoise" not in m]  # noqa: F405
