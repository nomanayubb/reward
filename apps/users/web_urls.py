"""Web page routes for the users module (dashboard, earn hub)."""
from django.urls import path

from .views import DashboardView, EarnHubView

urlpatterns = [
    path("", DashboardView.as_view(), name="dashboard"),
    path("earn/", EarnHubView.as_view(), name="earn-hub"),
]
