"""Web page routes for the offers module."""
from django.urls import path

from .views import OfferListPageView, OfferStartView

urlpatterns = [
    path("", OfferListPageView.as_view(), name="offer-list-page"),
    path("<uuid:pk>/start/", OfferStartView.as_view(), name="offer-start"),
]
