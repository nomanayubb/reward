"""Web page routes for the withdrawals module."""
from django.urls import path

from .views import WithdrawPageView

urlpatterns = [
    path("", WithdrawPageView.as_view(), name="withdraw-page"),
]
