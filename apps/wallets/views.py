"""Wallet API views and the wallet page.

Read-only balance information for the authenticated user. All balance
arithmetic stays in the ledger/service layer — views only serialize/render.
"""
from decimal import Decimal

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import WalletAccount
from .serializers import WalletSummarySerializer
from .services import POINTS_CURRENCY, SUPPORTED_CURRENCIES, get_wallet

ZERO = Decimal("0")


class WalletSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        wallet = get_wallet(request.user)
        accounts = list(wallet.accounts.all())

        by_currency: dict[str, dict[str, Decimal]] = {}
        for account in accounts:
            if account.currency not in SUPPORTED_CURRENCIES:
                continue
            by_currency.setdefault(account.currency, {})[account.type] = account.balance

        ordered_currencies = [wallet.currency] + [
            currency for currency in by_currency if currency != wallet.currency
        ]
        balances = [
            {
                "currency": currency,
                "cash": by_currency[currency].get(WalletAccount.Type.CASH, ZERO),
                "pending": by_currency[currency].get(WalletAccount.Type.PENDING, ZERO),
                "locked": by_currency[currency].get(WalletAccount.Type.LOCKED, ZERO),
                "bonus": by_currency[currency].get(WalletAccount.Type.BONUS, ZERO),
            }
            for currency in ordered_currencies
            if currency in by_currency
        ]

        primary = next(
            (bucket for bucket in balances if bucket["currency"] == wallet.currency),
            {"cash": ZERO, "pending": ZERO, "locked": ZERO, "bonus": ZERO},
        )
        points = next(
            (
                account.balance
                for account in accounts
                if account.type == WalletAccount.Type.POINTS and account.currency == POINTS_CURRENCY
            ),
            ZERO,
        )

        data = {
            "currency": wallet.currency,
            "cash": primary["cash"],
            "pending": primary["pending"],
            "locked": primary["locked"],
            "bonus": primary["bonus"],
            "points": points,
            "balances": balances,
            "accounts": [a for a in accounts if a.currency in SUPPORTED_CURRENCIES],
        }
        return Response(WalletSummarySerializer(data).data)


class WalletPageView(LoginRequiredMixin, TemplateView):
    """Server-rendered wallet page with per-currency balances."""

    template_name = "wallets/wallet.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        wallet = get_wallet(self.request.user)
        accounts = list(wallet.accounts.all())

        by_currency: dict[str, dict[str, Decimal]] = {}
        for account in accounts:
            if account.currency not in SUPPORTED_CURRENCIES:
                continue
            by_currency.setdefault(account.currency, {})[account.type] = account.balance

        context["wallet"] = wallet
        context["balances"] = by_currency
        context["points"] = next(
            (
                account.balance
                for account in accounts
                if account.type == WalletAccount.Type.POINTS
                and account.currency == POINTS_CURRENCY
            ),
            ZERO,
        )
        return context
