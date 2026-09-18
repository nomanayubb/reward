from django.apps import AppConfig


class CpaConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.cpa"
    label = "cpa"
    verbose_name = "CPA Provider Adapters"
