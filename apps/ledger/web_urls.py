"""Web page routes for the ledger module."""
from django.urls import path

from .views import TransactionPageView

urlpatterns = [
    path("", TransactionPageView.as_view(), name="transaction-page"),
]
