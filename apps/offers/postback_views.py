"""Provider postback endpoints (docs/DRD.md §23-24).

Thin transport layer: parse, hand to ``offers.services.process_postback``,
return the result. All validation and idempotency lives in the service.
"""
import json
import logging

from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from apps.cpa.models import CPAProvider

from .services import process_postback

logger = logging.getLogger(__name__)


@csrf_exempt
@require_POST
def provider_postback(request, provider_code: str):
    provider = get_object_or_404(CPAProvider, code=provider_code, is_enabled=True)

    try:
        payload = json.loads(request.body or b"{}")
    except json.JSONDecodeError:
        return JsonResponse({"ok": False, "error": "invalid_json"}, status=400)

    if not isinstance(payload, dict):
        payload = {"data": payload}

    headers = {key: value for key, value in request.headers.items()}
    conversion, created = process_postback(
        provider, payload, headers=headers, ip=request.META.get("REMOTE_ADDR")
    )

    if conversion is None:
        return JsonResponse({"ok": False, "error": "rejected"}, status=400)

    return JsonResponse(
        {
            "ok": True,
            "duplicate": not created,
            "conversion_id": str(conversion.id),
            "status": conversion.status,
        }
    )
