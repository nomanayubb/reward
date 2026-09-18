"""Deposit API views and the deposit page."""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.payments.models import PaymentProvider
from apps.payments.providers.base import (
    ProviderConfigurationError,
    ProviderRequestError,
)

from .forms import DepositForm
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


class DepositPageView(LoginRequiredMixin, TemplateView):
    """Server-rendered deposit page: create a payment and see instructions."""

    template_name = "deposits/deposit.html"

    def _providers(self):
        return PaymentProvider.objects.filter(is_enabled=True, supports_deposits=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.setdefault("form", DepositForm(providers=self._providers()))
        context["deposits"] = (
            Deposit.objects.filter(user=self.request.user)
            .select_related("provider")
            .order_by("-created_at")[:10]
        )
        return context

    def post(self, request, *args, **kwargs):
        providers = self._providers()
        form = DepositForm(request.POST, providers=providers)

        if form.is_valid():
            try:
                deposit = create_deposit(
                    user=request.user,
                    provider=form.cleaned_data["provider"],
                    amount=form.cleaned_data["amount"],
                )
            except (DepositError, ProviderConfigurationError, ProviderRequestError) as exc:
                form.add_error(None, str(exc))
            else:
                context = self.get_context_data(
                    form=DepositForm(providers=providers), created_deposit=deposit
                )
                return self.render_to_response(context)

        return self.render_to_response(self.get_context_data(form=form))
