"""KYC routes (mounted under /kyc/)."""
from django.urls import path

from .views import KYCPageView

urlpatterns = [
    path("", KYCPageView.as_view(), name="kyc-page"),
]
