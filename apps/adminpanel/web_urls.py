"""Web page routes for the admin panel (mounted under /admin-panel/)."""
from django.urls import path

from .views import (
    AdminAdActionView,
    AdminAdsView,
    AdminDashboardView,
    AdminFeatureFlagsView,
    AdminKYCActionView,
    AdminKYCQueueView,
    AdminProviderActionView,
    AdminProvidersView,
    AdminReportsView,
    AdminSettingsView,
    AdminUserActionView,
    AdminUserDetailView,
    AdminUserListView,
    WithdrawalActionView,
    WithdrawalQueueView,
)

urlpatterns = [
    path("", AdminDashboardView.as_view(), name="admin-dashboard"),
    path("withdrawals/", WithdrawalQueueView.as_view(), name="admin-withdrawals"),
    path(
        "withdrawals/<uuid:pk>/action/",
        WithdrawalActionView.as_view(),
        name="admin-withdrawal-action",
    ),
    path("users/", AdminUserListView.as_view(), name="admin-users"),
    path("users/<uuid:pk>/", AdminUserDetailView.as_view(), name="admin-user-detail"),
    path(
        "users/<uuid:pk>/action/",
        AdminUserActionView.as_view(),
        name="admin-user-action",
    ),
    path("settings/", AdminSettingsView.as_view(), name="admin-settings"),
    path("flags/", AdminFeatureFlagsView.as_view(), name="admin-flags"),
    path("providers/", AdminProvidersView.as_view(), name="admin-providers"),
    path(
        "providers/action/",
        AdminProviderActionView.as_view(),
        name="admin-provider-action",
    ),
    path("kyc/", AdminKYCQueueView.as_view(), name="admin-kyc"),
    path("kyc/<uuid:pk>/action/", AdminKYCActionView.as_view(), name="admin-kyc-action"),
    path("reports/", AdminReportsView.as_view(), name="admin-reports"),
    path("ads/", AdminAdsView.as_view(), name="admin-ads"),
    path("ads/<uuid:pk>/action/", AdminAdActionView.as_view(), name="admin-ad-action"),
]
