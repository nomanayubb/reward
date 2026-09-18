"""Serializers for the accounts module.

Registration delegates to ``apps.accounts.services.register_user`` so the
wallet/referral provisioning stays in one place.
"""
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "username",
            "phone",
            "country",
            "is_email_verified",
            "referral_code",
            "date_joined",
        )
        read_only_fields = fields


class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(
        write_only=True, min_length=8, style={"input_type": "password"}
    )
    username = serializers.CharField(required=False, allow_blank=True, max_length=50)
    referral_code = serializers.CharField(required=False, allow_blank=True, max_length=16)

    def validate_email(self, value: str) -> str:
        email = value.lower()
        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError("An account with this email already exists.")
        return email

    def validate_password(self, value: str) -> str:
        validate_password(value)
        return value

    def validate_username(self, value: str) -> str:
        if value and User.objects.filter(username=value).exists():
            raise serializers.ValidationError("This username is already taken.")
        return value

    def create(self, validated_data):
        from .services import register_user

        return register_user(
            email=validated_data["email"],
            password=validated_data["password"],
            username=validated_data.get("username") or None,
            referral_code=validated_data.get("referral_code", ""),
        )


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, style={"input_type": "password"})

    def validate(self, attrs):
        user = authenticate(
            request=self.context.get("request"),
            username=attrs["email"].lower(),
            password=attrs["password"],
        )
        if user is None or not user.is_active:
            raise serializers.ValidationError({"detail": "Invalid email or password."})
        attrs["user"] = user
        return attrs
