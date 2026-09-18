"""Offer routes (mounted under /api/v1/offers/)."""
from django.urls import path

from .views import OfferListView

urlpatterns = [
    path("", OfferListView.as_view(), name="offer-list"),
]
