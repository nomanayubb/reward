"""Per-page SEO overrides and structured data."""
from django.db import models

from apps.common.models import UUIDTimeStampedModel


class SEOConfig(UUIDTimeStampedModel):
    path = models.CharField(max_length=255, unique=True, help_text="e.g. /games/racing/")
    title = models.CharField(max_length=160, blank=True)
    meta_description = models.CharField(max_length=320, blank=True)
    canonical_url = models.URLField(max_length=500, blank=True)
    robots = models.CharField(max_length=64, default="index,follow")
    og_title = models.CharField(max_length=160, blank=True)
    og_description = models.CharField(max_length=320, blank=True)
    og_image = models.URLField(max_length=500, blank=True)
    schema_json = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["path"]
        verbose_name = "SEO configuration"
        verbose_name_plural = "SEO configurations"

    def __str__(self):
        return self.path
