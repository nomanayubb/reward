"""Serializers for the games module (catalog listing and sessions)."""
from rest_framework import serializers

from .models import Game, GameSession


class GameSerializer(serializers.ModelSerializer):
    category = serializers.CharField(source="category.name", read_only=True, default=None)

    class Meta:
        model = Game
        fields = (
            "id",
            "slug",
            "title",
            "description",
            "category",
            "thumbnail",
            "orientation",
            "min_session_seconds",
            "is_featured",
            "sort_order",
        )
        read_only_fields = fields


class GameSessionSerializer(serializers.ModelSerializer):
    game = serializers.SlugRelatedField(slug_field="slug", read_only=True)

    class Meta:
        model = GameSession
        fields = (
            "id",
            "game",
            "session_token",
            "status",
            "started_at",
            "ended_at",
            "duration_seconds",
            "score",
        )
        read_only_fields = fields
