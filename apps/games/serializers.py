"""Serializers for the games module (catalog listing)."""
from rest_framework import serializers

from .models import Game


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
