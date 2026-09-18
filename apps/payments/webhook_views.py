"""Payment provider webhook endpoints (NOWPayments, EasyPaisa, ...).

Signature verification is delegated to the provider adapter; crediting the
ledger is delegated to ``deposits.services.confirm_deposit``.
"""
import json
import logging

from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .models import PaymentProvider, PaymentTransaction

logger = logging.getLogger(__name__)


@csrf_exempt
@require_POST
def payment_webhook(request, provider_code: str):
    from .providers.base import load_adapter

    provider = get_object_or_404(PaymentProvider, code=provider_code, is_enabled=True)

    try:
        payload = json.loads(request.body or b"{}")
    except json.JSONDecodeError:
        return JsonResponse({"ok": False, "error": "invalid_json"}, status=400)

    headers = {key: value for key, value in request.headers.items()}

    try:
        adapter = load_adapter(provider)
    except Exception:
        logger.exception("No adapter configured for payment provider %s", provider.code)
        return JsonResponse({"ok": False, "error": "adapter_unavailable"}, status=500)

    if not adapter.verify_webhook(payload, headers):
        logger.warning("Invalid webhook signature from %s", provider.code)
        return JsonResponse({"ok": False, "error": "invalid_signature"}, status=400)

    result = adapter.parse_webhook(payload, headers)
    txn = PaymentTransaction.objects.filter(
        provider=provider, external_id=result.external_id
    ).first()
    if txn is None:
        return JsonResponse({"ok": False, "error": "unknown_transaction"}, status=404)

    txn.raw_payload = payload
    if result.status:
        txn.status = result.status
    txn.save(update_fields=["raw_payload", "status", "updated_at"])

    if result.status == PaymentTransaction.Status.CONFIRMED and txn.direction == PaymentTransaction.Direction.DEPOSIT:
        deposit = txn.deposits.first()
        if deposit is not None:
            from apps.deposits.services import confirm_deposit

            confirm_deposit(deposit, raw=payload)

    return JsonResponse({"ok": True})
