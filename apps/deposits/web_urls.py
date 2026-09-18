"""Web page routes for the deposits module."""
from django.urls import path

from .views import DepositPageView

urlpatterns = [
    path("", DepositPageView.as_view(), name="deposit-page"),
]
