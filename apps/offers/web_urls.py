"""Web page routes for the offers module."""
from django.urls import path

from .views import (
    OfferDetailView,
    OfferListPageView,
    OfferStartView,
    OfferwallIndexView,
    OfferwallProviderView,
)

urlpatterns = [
    path("", OfferListPageView.as_view(), name="offer-list-page"),
    path("offerwall/", OfferwallIndexView.as_view(), name="offerwall-index"),
    path("offerwall/<slug:code>/", OfferwallProviderView.as_view(), name="offerwall-provider"),
    path("<uuid:pk>/start/", OfferStartView.as_view(), name="offer-start"),
    path("<uuid:pk>/", OfferDetailView.as_view(), name="offer-detail"),
]
