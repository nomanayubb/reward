"""Ledger routes (mounted under /api/v1/ledger/)."""
from django.urls import path

from .views import LedgerTransactionListView

urlpatterns = [
    path("transactions/", LedgerTransactionListView.as_view(), name="ledger-transactions"),
]
