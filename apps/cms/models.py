"""CMS: editable pages (versioned) and the blog."""
from django.conf import settings
from django.db import models

from apps.common.models import TimeStampedModel, UUIDTimeStampedModel


class CMSPage(UUIDTimeStampedModel):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PUBLISHED = "published", "Published"

    slug = models.SlugField(max_length=160, unique=True)
    title = models.CharField(max_length=200)
    content = models.TextField(blank=True)
    status = models.CharField(
        max_length=16, choices=Status.choices, default=Status.DRAFT, db_index=True
    )
    published_at = models.DateTimeField(null=True, blank=True)

    seo_title = models.CharField(max_length=160, blank=True)
    seo_description = models.CharField(max_length=320, blank=True)

    class Meta:
        ordering = ["slug"]

    def __str__(self):
        return self.title


class PageVersion(UUIDTimeStampedModel):
    """Versioned terms/privacy pages — old versions stay retrievable."""

    page = models.ForeignKey(CMSPage, on_delete=models.CASCADE, related_name="versions")
    version = models.PositiveIntegerField()
    content = models.TextField()
    published_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=False)

    class Meta:
        ordering = ["-version"]
        constraints = [
            models.UniqueConstraint(fields=["page", "version"], name="uniq_page_version")
        ]

    def __str__(self):
        return f"{self.page.slug}:v{self.version}"


class BlogCategory(UUIDTimeStampedModel):
    name = models.CharField(max_length=80)
    slug = models.SlugField(max_length=80, unique=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "blog categories"

    def __str__(self):
        return self.name


class BlogPost(UUIDTimeStampedModel):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        SCHEDULED = "scheduled", "Scheduled"
        PUBLISHED = "published", "Published"

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="blog_posts"
    )
    category = models.ForeignKey(
        BlogCategory, null=True, blank=True, on_delete=models.SET_NULL, related_name="posts"
    )
    excerpt = models.TextField(blank=True)
    content = models.TextField(blank=True)
    featured_image = models.ImageField(upload_to="blog/", null=True, blank=True)
    tags = models.JSONField(default=list, blank=True)

    status = models.CharField(
        max_length=16, choices=Status.choices, default=Status.DRAFT, db_index=True
    )
    published_at = models.DateTimeField(null=True, blank=True, db_index=True)

    seo_title = models.CharField(max_length=160, blank=True)
    seo_description = models.CharField(max_length=320, blank=True)

    class Meta:
        ordering = ["-published_at", "-created_at"]

    def __str__(self):
        return self.title
