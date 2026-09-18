"""Base Django settings shared by every environment.

All environment-specific values are read from ``.env`` (see ``.env.example``).
Business values that admins may change at runtime (reward percentages,
points conversion, withdrawal limits, ...) are NOT stored here — they live in
the database and are resolved through ``apps.adminpanel`` configuration.
Settings here are only infrastructure defaults.
"""
from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env(
    DEBUG=(bool, False),
    ALLOWED_HOSTS=(list, ["localhost", "127.0.0.1"]),
)
env.read_env(str(BASE_DIR / ".env"))

# --------------------------------------------------------------------------
# Core
# --------------------------------------------------------------------------
SECRET_KEY = env("SECRET_KEY", default="insecure-dev-key-change-me")
DEBUG = env("DEBUG")
ALLOWED_HOSTS = env("ALLOWED_HOSTS")
SITE_URL = env("SITE_URL", default="http://localhost:8000")

# --------------------------------------------------------------------------
# Applications
# --------------------------------------------------------------------------
DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sitemaps",
    "django.contrib.humanize",
]

THIRD_PARTY_APPS = [
    "rest_framework",
    "drf_spectacular",
    "django_filters",
    "django_celery_beat",
    "whitenoise.runserver_nostatic",
]

LOCAL_APPS = [
    "apps.accounts",
    "apps.users",
    "apps.wallets",
    "apps.ledger",
    "apps.rewards",
    "apps.payments",
    "apps.deposits",
    "apps.withdrawals",
    "apps.games",
    "apps.surveys",
    "apps.offers",
    "apps.cpa",
    "apps.advertising",
    "apps.bonuses",
    "apps.referrals",
    "apps.fraud",
    "apps.risk",
    "apps.kyc",
    "apps.notifications",
    "apps.automation",
    "apps.analytics",
    "apps.reports",
    "apps.cms",
    "apps.seo",
    "apps.support",
    "apps.adminpanel",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# --------------------------------------------------------------------------
# Middleware
# --------------------------------------------------------------------------
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

# --------------------------------------------------------------------------
# Templates
# --------------------------------------------------------------------------
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# --------------------------------------------------------------------------
# Database — PostgreSQL in every real environment.
# --------------------------------------------------------------------------
DATABASES = {
    "default": env.db_url(
        "DATABASE_URL",
        default=f"sqlite:///{(BASE_DIR / 'db.sqlite3').as_posix()}",
    )
}
DATABASES["default"]["ATOMIC_REQUESTS"] = True
DATABASES["default"]["CONN_MAX_AGE"] = env.int("DB_CONN_MAX_AGE", default=60)

# --------------------------------------------------------------------------
# Authentication
# --------------------------------------------------------------------------
AUTH_USER_MODEL = "accounts.User"

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher",
    "django.contrib.auth.hashers.ScryptPasswordHasher",
]

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# --------------------------------------------------------------------------
# Internationalization (English + Urdu, RTL-ready)
# --------------------------------------------------------------------------
LANGUAGE_CODE = "en-us"
LANGUAGES = [
    ("en", "English"),
    ("ur", "Urdu"),
]
LOCALE_PATHS = [BASE_DIR / "locale"]
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# --------------------------------------------------------------------------
# Static & media
# --------------------------------------------------------------------------
STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --------------------------------------------------------------------------
# Cache / Redis
# --------------------------------------------------------------------------
REDIS_URL = env("REDIS_URL", default="redis://localhost:6379/0")
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": REDIS_URL,
    }
}

# --------------------------------------------------------------------------
# Celery
# --------------------------------------------------------------------------
CELERY_BROKER_URL = env("CELERY_BROKER_URL", default=REDIS_URL)
CELERY_RESULT_BACKEND = env("CELERY_RESULT_BACKEND", default=CELERY_BROKER_URL)
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = TIME_ZONE
CELERY_TASK_ACKS_LATE = True
CELERY_TASK_REJECT_ON_WORKER_LOST = True
CELERY_TASK_TIME_LIMIT = 60 * 10
CELERY_TASK_SOFT_TIME_LIMIT = 60 * 8
CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers:DatabaseScheduler"

CELERY_BEAT_SCHEDULE = {
    "sync-offers": {
        "task": "apps.offers.tasks.sync_offers",
        "schedule": 60 * 15,
    },
    "sync-surveys": {
        "task": "apps.surveys.tasks.sync_surveys",
        "schedule": 60 * 15,
    },
    "process-pending-rewards": {
        "task": "apps.rewards.tasks.process_pending_rewards",
        "schedule": 60 * 5,
    },
    "recalculate-campaign-quotas": {
        "task": "apps.offers.tasks.recalculate_campaign_quotas",
        "schedule": 60 * 5,
    },
    "expire-deposits": {
        "task": "apps.deposits.tasks.expire_deposits",
        "schedule": 60 * 10,
    },
    "fraud-analysis": {
        "task": "apps.fraud.tasks.run_fraud_analysis",
        "schedule": 60 * 30,
    },
    "daily-statistics": {
        "task": "apps.analytics.tasks.generate_daily_statistics",
        "schedule": 60 * 60 * 24,
    },
}

# --------------------------------------------------------------------------
# Django REST Framework
# --------------------------------------------------------------------------
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 25,
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "60/min",
        "user": "300/min",
        "login": "5/min",
        "withdrawal": "3/hour",
        "offer_click": "30/min",
        "postback": "120/min",
    },
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

SPECTACULAR_SETTINGS = {
    "TITLE": "Reward Platform API",
    "DESCRIPTION": "Rewards gaming, surveys and CPA platform API.",
    "VERSION": "0.1.0",
    "SERVE_INCLUDE_SCHEMA": False,
}

# --------------------------------------------------------------------------
# Email
# --------------------------------------------------------------------------
EMAIL_HOST = env("EMAIL_HOST", default="")
EMAIL_PORT = env.int("EMAIL_PORT", default=587)
EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")
EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=True)
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="noreply@example.com")

# --------------------------------------------------------------------------
# Platform defaults (runtime-overridable via PlatformSetting in the DB)
# --------------------------------------------------------------------------
PLATFORM_DEFAULTS = {
    "POINTS_PER_USD": 100,
    "DEFAULT_CURRENCY": "PKR",
    "SUPPORTED_CURRENCIES": ["PKR", "USD", "POINTS"],
    "EXCHANGE_RATE_USD_PKR": "280.00",
    # User-facing limits are expressed in PKR (ADR-015); other wallet
    # currencies convert from these values.
    "MIN_WITHDRAWAL_PKR": "500.00",
    "MAX_WITHDRAWAL_PKR": "100000.00",
    "KYC_THRESHOLD_PKR": "5000.00",
    "AUTO_PAYOUT_MAX_PKR": "1500.00",
    "DUAL_APPROVAL_THRESHOLD_PKR": "25000.00",
    # Emergency switches (admin panel → Providers)
    "GAMES_ENABLED": True,
    "OFFERS_ENABLED": True,
    "SURVEYS_ENABLED": True,
    "DEPOSITS_ENABLED": True,
    "WITHDRAWALS_ENABLED": True,
}

# Root folder holding self-contained HTML5 games (see docs/GAME_INTEGRATION.md)
GAMES_ROOT = BASE_DIR / "games"

# --------------------------------------------------------------------------
# Payment providers (secrets come from the environment; never hard-code)
# --------------------------------------------------------------------------
NOWPAYMENTS_API_KEY = env("NOWPAYMENTS_API_KEY", default="")
NOWPAYMENTS_IPN_SECRET = env("NOWPAYMENTS_IPN_SECRET", default="")
NOWPAYMENTS_SANDBOX = env.bool("NOWPAYMENTS_SANDBOX", default=True)

# --------------------------------------------------------------------------
# Logging
# --------------------------------------------------------------------------
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {name} {process:d} {thread:d} {message}",
            "style": "{",
        },
        "simple": {"format": "{levelname} {asctime} {name} {message}", "style": "{"},
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "verbose"},
    },
    "root": {"handlers": ["console"], "level": "INFO"},
    "loggers": {
        "django": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "django.security": {"handlers": ["console"], "level": "WARNING", "propagate": False},
        "apps": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "celery": {"handlers": ["console"], "level": "INFO", "propagate": False},
    },
}
