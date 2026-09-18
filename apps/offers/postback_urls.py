"""Postback URLs for CPA providers: /api/v1/postbacks/<provider_code>/"""
from django.urls import path

from .postback_views import provider_postback

urlpatterns = [
    path("<str:provider_code>/", provider_postback, name="provider-postback"),
]
