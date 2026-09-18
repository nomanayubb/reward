"""Web page routes for the offers module."""
from django.urls import path

from .views import OfferListPageView

urlpatterns = [
    path("", OfferListPageView.as_view(), name="offer-list-page"),
]
