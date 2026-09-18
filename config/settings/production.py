"""Production settings — secure by default, all secrets from the environment.

Host-agnostic: the same image runs on your own VPS, Render, Railway or any
container host. Everything that differs between hosts is an environment
variable, never code.
"""
from .base import *  # noqa: F401,F403

DEBUG = False

# ---------------------------------------------------------------------------
# Hosts and trusted origins — all environment-driven.
#   ALLOWED_HOSTS        e.g. "example.com,www.example.com"
#   EXTRA_ALLOWED_HOSTS  additional hosts (staging, preview URLs, ...)
#   CSRF_TRUSTED_ORIGINS e.g. "https://example.com,https://www.example.com"
# ---------------------------------------------------------------------------
ALLOWED_HOSTS = env("ALLOWED_HOSTS")  # noqa: F405
ALLOWED_HOSTS += env.list("EXTRA_ALLOWED_HOSTS", default=[])  # noqa: F405

CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=[])  # noqa: F405

# Optional convenience only: Render announces its hostname in this variable.
# It is ignored on any other host and can be deleted without side effects.
_render_host = env("RENDER_EXTERNAL_HOSTNAME", default="")  # noqa: F405
if _render_host:
    ALLOWED_HOSTS.append(_render_host)
    CSRF_TRUSTED_ORIGINS.append(f"https://{_render_host}")

# Redis is used when available; free single-instance hosts can run without it.
REDIS_URL = env("REDIS_URL", default="")  # noqa: F405
if REDIS_URL:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.redis.RedisCache",
            "LOCATION": REDIS_URL,
        }
    }
else:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "reward-prod",
        }
    }

# Transport / cookie security
SECURE_SSL_REDIRECT = env.bool("SECURE_SSL_REDIRECT", default=True)  # noqa: F405
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"
SECURE_HSTS_SECONDS = 60 * 60 * 24 * 30
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
X_FRAME_OPTIONS = "DENY"

# Reverse-proxy awareness for whitenoise
WHITENOISE_MAX_AGE = 60 * 60 * 24 * 30
