"""Web page routes for the users module (dashboard)."""
from django.urls import path

from .views import DashboardView

urlpatterns = [
    path("", DashboardView.as_view(), name="dashboard"),
]
