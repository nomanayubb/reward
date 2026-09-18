"""Wallet API views.

Read-only balance information for the authenticated user. All balance
arithmetic stays in the ledger/service layer — this view only serializes.
"""
from decimal import Decimal

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import WalletAccount
from .serializers import WalletSummarySerializer
from .services import POINTS_CURRENCY, get_wallet


class WalletSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        wallet = get_wallet(request.user)
        accounts = list(wallet.accounts.all())

        money_accounts = [account for account in accounts if account.currency == wallet.currency]
        by_type = {account.type: account.balance for account in money_accounts}
        points = next(
            (
                account.balance
                for account in accounts
                if account.type == WalletAccount.Type.POINTS
                and account.currency == POINTS_CURRENCY
            ),
            Decimal("0"),
        )

        data = {
            "currency": wallet.currency,
            "cash": by_type.get(WalletAccount.Type.CASH, Decimal("0")),
            "pending": by_type.get(WalletAccount.Type.PENDING, Decimal("0")),
            "locked": by_type.get(WalletAccount.Type.LOCKED, Decimal("0")),
            "bonus": by_type.get(WalletAccount.Type.BONUS, Decimal("0")),
            "points": points,
            "accounts": money_accounts,
        }
        return Response(WalletSummarySerializer(data).data)
