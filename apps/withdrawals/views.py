"""Withdrawal API views and the withdrawal page."""
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.views.generic import TemplateView
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .forms import WithdrawalMethodForm, WithdrawForm
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


class WithdrawPageView(LoginRequiredMixin, TemplateView):
    """Server-rendered withdrawal page: methods, request form, history."""

    template_name = "withdrawals/withdraw.html"

    def _methods(self):
        return WithdrawalMethod.objects.filter(
            user=self.request.user, disabled_at__isnull=True
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        methods = self._methods()
        context.setdefault("form", WithdrawForm(methods=methods))
        context.setdefault("method_form", WithdrawalMethodForm())
        context["methods"] = methods
        context["withdrawals"] = (
            Withdrawal.objects.filter(user=self.request.user)
            .select_related("method")
            .order_by("-requested_at")[:10]
        )
        return context

    def post(self, request, *args, **kwargs):
        methods = self._methods()

        if request.POST.get("action") == "add_method":
            method_form = WithdrawalMethodForm(request.POST)
            if method_form.is_valid():
                data = method_form.cleaned_data
                WithdrawalMethod.objects.create(
                    user=request.user,
                    type=data["type"],
                    label=data.get("label", ""),
                    details={"account_number": data["account_number"]},
                )
                messages.success(request, "Payout method added.")
                return redirect("withdraw-page")
            return self.render_to_response(self.get_context_data(method_form=method_form))

        form = WithdrawForm(request.POST, methods=methods)
        if form.is_valid():
            try:
                request_withdrawal(
                    user=request.user,
                    method=form.cleaned_data["method"],
                    amount=form.cleaned_data["amount"],
                )
            except WithdrawalError as exc:
                form.add_error(None, str(exc))
            else:
                messages.success(
                    request, "Withdrawal requested — funds are reserved while it is reviewed."
                )
                return redirect("withdraw-page")
        return self.render_to_response(self.get_context_data(form=form))
