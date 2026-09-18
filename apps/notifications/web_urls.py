"""Web page routes for the notifications module."""
from django.urls import path

from .views import NotificationPageView

urlpatterns = [
    path("", NotificationPageView.as_view(), name="notification-page"),
]
