"""Serializers for the ledger module (read-only history)."""
from rest_framework import serializers

from .models import LedgerEntry


class LedgerEntrySerializer(serializers.ModelSerializer):
    transaction_id = serializers.UUIDField(source="transaction.id", read_only=True)
    type = serializers.CharField(source="transaction.type", read_only=True)
    status = serializers.CharField(source="transaction.status", read_only=True)
    reference = serializers.CharField(source="transaction.reference", read_only=True)
    description = serializers.CharField(source="transaction.description", read_only=True)
    account_type = serializers.CharField(source="account.type", read_only=True)
    currency = serializers.CharField(source="account.currency", read_only=True)

    class Meta:
        model = LedgerEntry
        fields = (
            "id",
            "transaction_id",
            "type",
            "status",
            "amount",
            "currency",
            "account_type",
            "reference",
            "description",
            "created_at",
        )
        read_only_fields = fields
