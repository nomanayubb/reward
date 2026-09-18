"""Serializers for the deposits module."""
from decimal import Decimal

from rest_framework import serializers

from .models import Deposit


class DepositSerializer(serializers.ModelSerializer):
    provider = serializers.CharField(source="provider.name", read_only=True)

    class Meta:
        model = Deposit
        fields = (
            "id",
            "provider",
            "amount",
            "currency",
            "status",
            "payment_instructions",
            "expires_at",
            "confirmed_at",
            "created_at",
        )
        read_only_fields = fields


class DepositCreateSerializer(serializers.Serializer):
    provider = serializers.CharField(max_length=64)
    amount = serializers.DecimalField(
        max_digits=20, decimal_places=8, min_value=Decimal("0.01")
    )
    currency = serializers.CharField(required=False, allow_blank=True, max_length=8)
