"""HTML5 games: catalog, reward rules, sessions and events.

Games are self-contained folders under ``games/<slug>/`` (see
docs/GAME_INTEGRATION.md). The platform wraps them via the Game SDK; scores and
events from the client are never trusted for money — server-side validation and
``GameRewardRule`` conditions decide rewards.
"""
from django.conf import settings
from django.db import models

from apps.common.fields import money_field
from apps.common.models import TimeStampedModel, UUIDTimeStampedModel


class GameCategory(UUIDTimeStampedModel):
    name = models.CharField(max_length=80)
    slug = models.SlugField(max_length=80, unique=True)
    description = models.TextField(blank=True)
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["sort_order", "name"]
        verbose_name_plural = "game categories"

    def __str__(self):
        return self.name


class Game(UUIDTimeStampedModel):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        PAUSED = "paused", "Paused"
        MAINTENANCE = "maintenance", "Maintenance"
        RETIRED = "retired", "Retired"

    slug = models.SlugField(max_length=80, unique=True)
    title = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    category = models.ForeignKey(
        GameCategory, null=True, blank=True, on_delete=models.SET_NULL, related_name="games"
    )

    entry_path = models.CharField(
        max_length=255, help_text="Relative path under games/, e.g. 'flappy-example/game.html'"
    )
    thumbnail = models.ImageField(upload_to="games/thumbs/", null=True, blank=True)
    orientation = models.CharField(max_length=16, blank=True)

    status = models.CharField(
        max_length=16, choices=Status.choices, default=Status.ACTIVE, db_index=True
    )
    is_featured = models.BooleanField(default=False)
    sort_order = models.PositiveIntegerField(default=0)

    min_session_seconds = models.PositiveIntegerField(
        default=30, help_text="Server-side minimum play time before rewards are considered."
    )
    max_daily_sessions = models.PositiveIntegerField(default=20)

    seo_title = models.CharField(max_length=160, blank=True)
    seo_description = models.CharField(max_length=320, blank=True)

    class Meta:
        ordering = ["sort_order", "title"]
        indexes = [models.Index(fields=["status", "is_featured"])]

    def __str__(self):
        return self.title


class GameRewardRule(UUIDTimeStampedModel):
    class Mode(models.TextChoices):
        POINTS = "points", "Points"
        CASH = "cash", "Cash"

    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name="reward_rules")
    name = models.CharField(max_length=120)
    is_active = models.BooleanField(default=True)
    priority = models.PositiveIntegerField(default=100)

    conditions = models.JSONField(
        default=dict, blank=True,
        help_text='e.g. {"min_score": 1000} or {"min_duration_seconds": 600}',
    )
    mode = models.CharField(max_length=16, choices=Mode.choices, default=Mode.POINTS)
    points = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    cash = money_field()

    cooldown_hours = models.PositiveIntegerField(default=24)
    daily_max = models.PositiveIntegerField(default=1)
    monthly_max = models.PositiveIntegerField(default=20)

    class Meta:
        ordering = ["priority", "name"]

    def __str__(self):
        return f"{self.game.slug}:{self.name}"


class GameSession(UUIDTimeStampedModel):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        ENDED = "ended", "Ended"
        INVALIDATED = "invalidated", "Invalidated (anti-cheat)"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="game_sessions"
    )
    game = models.ForeignKey(Game, on_delete=models.PROTECT, related_name="sessions")
    session_token = models.CharField(max_length=64, unique=True)

    status = models.CharField(
        max_length=16, choices=Status.choices, default=Status.ACTIVE, db_index=True
    )
    started_at = models.DateTimeField(auto_now_add=True, db_index=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    duration_seconds = models.PositiveIntegerField(default=0)
    score = models.BigIntegerField(null=True, blank=True)

    ip_address = models.GenericIPAddressField(null=True, blank=True)
    device_id_hash = models.CharField(max_length=128, blank=True)
    invalid_reason = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["-started_at"]
        indexes = [
            models.Index(fields=["user", "game", "started_at"]),
            models.Index(fields=["game", "status"]),
        ]

    def __str__(self):
        return f"session:{self.game_id}:{self.user_id}"


class GameEvent(UUIDTimeStampedModel):
    session = models.ForeignKey(GameSession, on_delete=models.CASCADE, related_name="events")
    event_type = models.CharField(max_length=64, db_index=True)
    payload = models.JSONField(default=dict, blank=True)
    server_validated = models.BooleanField(default=False)
    validation_note = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["created_at"]
        indexes = [models.Index(fields=["session", "event_type"])]

    def __str__(self):
        return f"event:{self.event_type}:{self.session_id}"
