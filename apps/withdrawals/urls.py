"""Withdrawal routes (mounted under /api/v1/withdrawals/)."""
from django.urls import path

from .views import WithdrawalListCreateView, WithdrawalMethodListCreateView

urlpatterns = [
    path("", WithdrawalListCreateView.as_view(), name="withdrawal-list-create"),
    path("methods/", WithdrawalMethodListCreateView.as_view(), name="withdrawal-methods"),
]
