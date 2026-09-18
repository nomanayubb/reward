"""Public routes for the CMS (landing page and static pages)."""
from django.urls import path

from .views import CMSPageView, PublicHomeView

urlpatterns = [
    path("", PublicHomeView.as_view(), name="public-home"),
    path("p/<slug:slug>/", CMSPageView.as_view(), name="cms-page"),
]
