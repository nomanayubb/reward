"""Wallet routes (mounted under /api/v1/wallets/)."""
from django.urls import path

from .views import WalletSummaryView

urlpatterns = [
    path("summary/", WalletSummaryView.as_view(), name="wallet-summary"),
]
