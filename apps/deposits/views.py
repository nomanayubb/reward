"""Deposit API views: list deposits and create payment requests."""
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.payments.models import PaymentProvider

from .models import Deposit
from .serializers import DepositCreateSerializer, DepositSerializer
from .services import DepositError, create_deposit


class DepositListCreateView(generics.ListCreateAPIView):
    """``GET`` the user's deposits, ``POST`` a new payment request."""

    permission_classes = [IsAuthenticated]
    serializer_class = DepositSerializer

    def get_queryset(self):
        return (
            Deposit.objects.filter(user=self.request.user)
            .select_related("provider")
            .order_by("-created_at")
        )

    def create(self, request, *args, **kwargs):
        serializer = DepositCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        provider = PaymentProvider.objects.filter(
            code=serializer.validated_data["provider"],
            is_enabled=True,
            supports_deposits=True,
        ).first()
        if provider is None:
            return Response(
                {"detail": "Unknown or disabled payment provider."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            deposit = create_deposit(
                user=request.user,
                provider=provider,
                amount=serializer.validated_data["amount"],
                currency=serializer.validated_data.get("currency") or None,
            )
        except DepositError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(DepositSerializer(deposit).data, status=status.HTTP_201_CREATED)
