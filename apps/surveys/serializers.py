"""Serializers for the surveys module (user-facing catalog)."""
from rest_framework import serializers

from .models import Survey


class SurveySerializer(serializers.ModelSerializer):
    provider = serializers.CharField(source="provider.name", read_only=True)

    class Meta:
        model = Survey
        fields = (
            "id",
            "title",
            "description",
            "provider",
            "category",
            "country",
            "language",
            "device",
            "estimated_minutes",
            "payout",
            "user_reward",
            "currency",
            "reward_mode",
            "qualification_rate",
            "expires_at",
        )
        read_only_fields = fields
