"""Serializers for the withdrawals module."""
from decimal import Decimal

from rest_framework import serializers

from .models import Withdrawal, WithdrawalMethod


class WithdrawalMethodSerializer(serializers.ModelSerializer):
    class Meta:
        model = WithdrawalMethod
        fields = (
            "id",
            "type",
            "label",
            "details",
            "is_default",
            "is_verified",
            "created_at",
        )
        read_only_fields = ("id", "is_verified", "created_at")


class WithdrawalMethodCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = WithdrawalMethod
        fields = ("type", "label", "details")

    def validate_details(self, value):
        if not isinstance(value, dict) or not value:
            raise serializers.ValidationError("Provide the account details for this method.")
        return value


class WithdrawalSerializer(serializers.ModelSerializer):
    method_type = serializers.CharField(source="method.type", read_only=True)
    method_label = serializers.CharField(source="method.label", read_only=True)

    class Meta:
        model = Withdrawal
        fields = (
            "id",
            "amount",
            "fee",
            "net_amount",
            "currency",
            "status",
            "risk_level",
            "payout_mode",
            "method_type",
            "method_label",
            "payment_reference",
            "rejection_reason",
            "requested_at",
            "reviewed_at",
            "paid_at",
        )
        read_only_fields = fields


class WithdrawalCreateSerializer(serializers.Serializer):
    method = serializers.PrimaryKeyRelatedField(queryset=WithdrawalMethod.objects.all())
    amount = serializers.DecimalField(
        max_digits=20, decimal_places=8, min_value=Decimal("0.01")
    )
    currency = serializers.CharField(required=False, allow_blank=True, max_length=8)

    def validate_method(self, value):
        request = self.context["request"]
        if value.user_id != request.user.id:
            raise serializers.ValidationError("Unknown withdrawal method.")
        return value
