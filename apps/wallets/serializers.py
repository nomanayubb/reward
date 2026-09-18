"""Serializers for the wallets module."""
from rest_framework import serializers

from .models import WalletAccount


class WalletAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = WalletAccount
        fields = ("id", "type", "currency", "balance", "is_frozen")
        read_only_fields = fields


class CurrencyBalanceSerializer(serializers.Serializer):
    """Per-currency bucket of a user's wallet (ADR-015: PKR + USD)."""

    currency = serializers.CharField()
    cash = serializers.DecimalField(max_digits=20, decimal_places=8)
    pending = serializers.DecimalField(max_digits=20, decimal_places=8)
    locked = serializers.DecimalField(max_digits=20, decimal_places=8)
    bonus = serializers.DecimalField(max_digits=20, decimal_places=8)


class WalletSummarySerializer(serializers.Serializer):
    """Dashboard-ready balance summary (all values read-only).

    Top-level cash/pending/locked/bonus describe the primary currency; the
    ``balances`` list carries every supported currency the user holds.
    """

    currency = serializers.CharField()
    cash = serializers.DecimalField(max_digits=20, decimal_places=8)
    pending = serializers.DecimalField(max_digits=20, decimal_places=8)
    locked = serializers.DecimalField(max_digits=20, decimal_places=8)
    bonus = serializers.DecimalField(max_digits=20, decimal_places=8)
    points = serializers.DecimalField(max_digits=20, decimal_places=8)
    balances = CurrencyBalanceSerializer(many=True)
    accounts = WalletAccountSerializer(many=True)
