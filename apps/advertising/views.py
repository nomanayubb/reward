"""Advertising API/page views: click tracking and the rendered ad slot."""
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_GET

from .models import AdImpression
from .services import record_click


@require_GET
def ad_click(request, impression_id):
    """Record a click and forward to the advertiser's landing page."""
    impression = get_object_or_404(AdImpression, pk=impression_id)
    record_click(impression=impression, user=request.user, ip=request.META.get("REMOTE_ADDR"))

    target = impression.campaign.target_url
    if not target:
        return redirect("dashboard")
    return redirect(target)
