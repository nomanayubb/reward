"""Serializers for the offers module (user-facing catalog)."""
from rest_framework import serializers

from .models import Offer


class OfferSerializer(serializers.ModelSerializer):
    """Public offer fields only — no tracking URLs or internal flags.

    Compliance fields are exposed so the UI can show the user exactly what the
    campaign permits (DRD §204: never hide important conditions). Remaining
    completion counts are computed per requesting user.
    """

    provider = serializers.CharField(source="provider.name", read_only=True)
    category = serializers.CharField(source="category.name", read_only=True, default=None)
    daily_remaining = serializers.SerializerMethodField()
    lifetime_remaining = serializers.SerializerMethodField()
    campaign_remaining = serializers.SerializerMethodField()
    next_reset_at = serializers.SerializerMethodField()

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
            "daily_remaining",
            "lifetime_remaining",
            "campaign_remaining",
            "next_reset_at",
        )
        read_only_fields = fields

    def _limits(self, offer):
        if not hasattr(offer, "_limit_status"):
            from .services import limit_status

            request = self.context.get("request")
            offer._limit_status = (
                limit_status(request.user, offer) if request is not None else None
            )
        return offer._limit_status or {}

    def get_daily_remaining(self, offer):
        return self._limits(offer).get("daily_remaining")

    def get_lifetime_remaining(self, offer):
        return self._limits(offer).get("lifetime_remaining")

    def get_campaign_remaining(self, offer):
        return self._limits(offer).get("campaign_remaining")

    def get_next_reset_at(self, offer):
        return self._limits(offer).get("next_reset_at")
