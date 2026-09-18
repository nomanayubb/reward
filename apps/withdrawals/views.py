"""Withdrawal API views: list/request withdrawals and manage payout methods."""
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Withdrawal, WithdrawalMethod
from .serializers import (
    WithdrawalCreateSerializer,
    WithdrawalMethodCreateSerializer,
    WithdrawalMethodSerializer,
    WithdrawalSerializer,
)
from .services import WithdrawalError, request_withdrawal


class WithdrawalListCreateView(generics.ListCreateAPIView):
    """``GET`` the user's withdrawals, ``POST`` a new request.

    Optional list filter: ``?status=requested|under_review|approved|...``
    """

    permission_classes = [IsAuthenticated]
    serializer_class = WithdrawalSerializer

    def get_queryset(self):
        queryset = (
            Withdrawal.objects.filter(user=self.request.user)
            .select_related("method")
            .order_by("-requested_at")
        )
        status_filter = self.request.query_params.get("status")
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        return queryset

    def create(self, request, *args, **kwargs):
        serializer = WithdrawalCreateSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        try:
            withdrawal = request_withdrawal(
                user=request.user,
                method=serializer.validated_data["method"],
                amount=serializer.validated_data["amount"],
                currency=serializer.validated_data.get("currency") or None,
            )
        except WithdrawalError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(WithdrawalSerializer(withdrawal).data, status=status.HTTP_201_CREATED)


class WithdrawalMethodListCreateView(generics.ListCreateAPIView):
    """``GET`` the user's payout methods, ``POST`` a new one."""

    permission_classes = [IsAuthenticated]
    serializer_class = WithdrawalMethodSerializer

    def get_queryset(self):
        return WithdrawalMethod.objects.filter(user=self.request.user).order_by(
            "-is_default", "created_at"
        )

    def create(self, request, *args, **kwargs):
        serializer = WithdrawalMethodCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        method = WithdrawalMethod.objects.create(user=request.user, **serializer.validated_data)
        return Response(
            WithdrawalMethodSerializer(method).data, status=status.HTTP_201_CREATED
        )
