"""Serializers for the offers module (user-facing catalog)."""
from rest_framework import serializers

from .models import Offer


class OfferSerializer(serializers.ModelSerializer):
    """Public offer fields only — no tracking URLs or internal flags.

    Compliance fields are exposed so the UI can show the user exactly what the
    campaign permits (DRD §204: never hide important conditions).
    """

    provider = serializers.CharField(source="provider.name", read_only=True)
    category = serializers.CharField(source="category.name", read_only=True, default=None)

    class Meta:
        model = Offer
        fields = (
            "id",
            "title",
            "description",
            "advertiser",
            "provider",
            "category",
            "payout",
            "user_reward",
            "currency",
            "reward_mode",
            "points_reward",
            "countries",
            "devices",
            "min_age",
            "daily_user_limit",
            "lifetime_user_limit",
            "multiple_completion_allowed",
            "reinstall_allowed",
            "is_featured",
            "expires_at",
        )
        read_only_fields = fields
