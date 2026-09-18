"""Web page routes for the admin panel (mounted under /admin-panel/)."""
from django.urls import path

from .views import AdminDashboardView, WithdrawalActionView, WithdrawalQueueView

urlpatterns = [
    path("", AdminDashboardView.as_view(), name="admin-dashboard"),
    path("withdrawals/", WithdrawalQueueView.as_view(), name="admin-withdrawals"),
    path(
        "withdrawals/<uuid:pk>/action/",
        WithdrawalActionView.as_view(),
        name="admin-withdrawal-action",
    ),
]
