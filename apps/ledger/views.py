"""Ledger API views and the transaction history page."""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated

from .models import LedgerEntry
from .serializers import LedgerEntrySerializer


class LedgerTransactionListView(ListAPIView):
    """Paginated ledger entries belonging to the current user.

    Optional filters: ``?type=reward|reversal|deposit|withdrawal_payout...``
    and ``?status=pending|posted|reversed``.
    """

    serializer_class = LedgerEntrySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = (
            LedgerEntry.objects.filter(account__wallet__user=self.request.user)
            .select_related("transaction", "account")
            .order_by("-created_at")
        )
        entry_type = self.request.query_params.get("type")
        if entry_type:
            queryset = queryset.filter(transaction__type=entry_type)
        status = self.request.query_params.get("status")
        if status:
            queryset = queryset.filter(transaction__status=status)
        return queryset


class TransactionPageView(LoginRequiredMixin, ListView):
    """Server-rendered transaction history."""

    template_name = "ledger/transactions.html"
    context_object_name = "entries"
    paginate_by = 25

    def get_queryset(self):
        return (
            LedgerEntry.objects.filter(account__wallet__user=self.request.user)
            .select_related("transaction", "account")
            .order_by("-created_at")
        )
