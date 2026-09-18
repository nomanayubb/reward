"""Webhook URLs for payment providers: /api/v1/webhooks/<provider_code>/"""
from django.urls import path

from .webhook_views import payment_webhook

urlpatterns = [
    path("<str:provider_code>/", payment_webhook, name="payment-webhook"),
]
