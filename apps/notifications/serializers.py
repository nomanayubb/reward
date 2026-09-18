"""Serializers for the notifications module."""
from rest_framework import serializers

from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = (
            "id",
            "kind",
            "channel",
            "title",
            "body",
            "metadata",
            "is_read",
            "read_at",
            "created_at",
        )
        read_only_fields = fields
