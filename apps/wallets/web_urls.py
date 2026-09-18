"""Web page routes for the wallets module."""
from django.urls import path

from .views import WalletPageView

urlpatterns = [
    path("", WalletPageView.as_view(), name="wallet-page"),
]
