"""Adapter scaffolding for new provider networks (flexibility tooling).

Adding a network should be: scaffold → fill the parsing/signature methods →
add credentials → register in the admin. No core changes (ADR-003).
"""
from pathlib import Path

from django.conf import settings

CPA_TEMPLATE = '''"""{name} CPA adapter (scaffolded).

STATUS: **not implemented** — fill the TODOs using {name}'s publisher docs and
a sample postback, then enable the provider in the admin.

Required env keys: {env_prefix}_API_KEY, {env_prefix}_SECRET
"""
import hashlib
import hmac
from decimal import Decimal

from apps.cpa.providers.base import (
    CPAProviderAdapter,
    NormalizedConversion,
    NormalizedOffer,
)


class {class_name}Adapter(CPAProviderAdapter):
    code = "{code}"

    def get_offers(self) -> list[NormalizedOffer]:
        """Fetch the offer feed. TODO: call the {name} API/feed URL."""
        raise NotImplementedError("Implement get_offers for {name}.")

    def process_postback(
        self, payload: dict, headers: dict | None = None, raw_body: bytes | None = None
    ) -> NormalizedConversion:
        """Map the provider payload into our normalized conversion. TODO: verify field names."""
        return NormalizedConversion(
            external_conversion_id=str(payload.get("transaction_id", "")),
            user_identifier=str(payload.get("subid", "")),
            payout=Decimal(str(payload.get("amount", "0") or "0")),
            status="approved" if str(payload.get("status")) in {"1", "approved"} else "rejected",
            offer_external_id=str(payload.get("offer_id", "")),
            raw=payload,
        )

    def validate_signature(
        self, payload: dict, headers: dict | None = None, raw_body: bytes | None = None
    ) -> bool:
        """TODO: replace with the provider's documented signature algorithm."""
        secret = self.config.get("secret", "")
        if not secret:
            return False
        signature = (headers or {}).get("x-signature", "")
        expected = hmac.new(
            secret.encode(), (raw_body or str(payload).encode()), hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(expected, signature)
'''

SURVEY_TEMPLATE = '''"""{name} survey adapter (scaffolded).

STATUS: **not implemented** — fill the TODOs using {name}'s publisher docs.

Required env keys: {env_prefix}_API_KEY, {env_prefix}_SECRET
"""
import hashlib
import hmac
from decimal import Decimal

from apps.surveys.providers.base import (
    NormalizedSurvey,
    NormalizedSurveyCompletion,
    SurveyProviderAdapter,
)


class {class_name}Adapter(SurveyProviderAdapter):
    code = "{code}"

    def get_surveys(self, user=None) -> list[NormalizedSurvey]:
        """Fetch available surveys. TODO: call the {name} API."""
        raise NotImplementedError("Implement get_surveys for {name}.")

    def get_survey_url(self, survey, user, session) -> str:
        """Return the URL the user should open for this survey. TODO."""
        raise NotImplementedError("Implement get_survey_url for {name}.")

    def process_postback(
        self, payload: dict, headers: dict | None = None
    ) -> NormalizedSurveyCompletion:
        """Map the provider completion payload. TODO: verify field names."""
        return NormalizedSurveyCompletion(
            external_completion_id=str(payload.get("transaction_id", "")),
            user_identifier=str(payload.get("subid", "")),
            payout=Decimal(str(payload.get("amount", "0") or "0")),
            survey_external_id=str(payload.get("survey_id", "")),
            status="approved" if str(payload.get("status")) in {"1", "approved"} else "rejected",
            raw=payload,
        )

    def validate_signature(self, payload: dict, headers: dict | None = None) -> bool:
        """TODO: replace with the provider's documented signature algorithm."""
        secret = self.config.get("secret", "")
        if not secret:
            return False
        signature = (headers or {}).get("x-signature", "")
        expected = hmac.new(
            secret.encode(), str(payload).encode(), hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(expected, signature)
'''

PAYMENT_TEMPLATE = '''"""{name} payment adapter (scaffolded).

STATUS: **not implemented** — fill the TODOs using {name}'s merchant docs.

Required env keys: {env_prefix}_API_KEY, {env_prefix}_SECRET
"""
from decimal import Decimal

from apps.payments.providers.base import (
    CreatedPayment,
    PaymentProviderAdapter,
    PaymentStatusResult,
)


class {class_name}Adapter(PaymentProviderAdapter):
    code = "{code}"

    def create_payment(self, *, amount, currency: str, reference: str, user=None) -> CreatedPayment:
        """Create a payment request. TODO: call the {name} API."""
        raise NotImplementedError("Implement create_payment for {name}.")

    def check_payment(self, external_id: str) -> PaymentStatusResult:
        """Fetch the payment status. TODO."""
        raise NotImplementedError("Implement check_payment for {name}.")

    def verify_webhook(self, payload: dict, headers: dict | None = None) -> bool:
        """TODO: verify the provider signature before trusting the payload."""
        return False

    def parse_webhook(self, payload: dict, headers: dict | None = None) -> PaymentStatusResult:
        """Map the webhook payload to our statuses. TODO: verify field names."""
        return PaymentStatusResult(
            external_id=str(payload.get("payment_id", "")),
            status="confirming",
            amount=Decimal(str(payload.get("amount", "0") or "0")),
            currency=str(payload.get("currency", "")).upper(),
            raw=payload,
        )

    def create_payout(self, *, amount, currency: str, destination: dict, reference: str) -> dict:
        """TODO: only implement after the payout API is verified with the provider."""
        raise NotImplementedError("Implement create_payout for {name}.")
'''

TEMPLATES = {
    "cpa": CPA_TEMPLATE,
    "survey": SURVEY_TEMPLATE,
    "payment": PAYMENT_TEMPLATE,
}

APP_FOR_KIND = {
    "cpa": "cpa",
    "survey": "surveys",
    "payment": "payments",
}


def class_name_for(code: str) -> str:
    return "".join(part.capitalize() for part in code.replace("-", "_").split("_"))


def module_name_for(code: str) -> str:
    return code.replace("-", "_").lower()


def env_prefix_for(code: str) -> str:
    return code.replace("-", "_").upper()


def render_adapter(kind: str, code: str, name: str) -> str:
    template = TEMPLATES[kind]
    return (
        template.replace("{name}", name)
        .replace("{code}", code)
        .replace("{class_name}", class_name_for(code))
        .replace("{env_prefix}", env_prefix_for(code))
    )


def adapter_path_for(kind: str, code: str) -> str:
    app = APP_FOR_KIND[kind]
    return f"apps.{app}.providers.{module_name_for(code)}.{class_name_for(code)}Adapter"


def target_path(kind: str, code: str) -> Path:
    app = APP_FOR_KIND[kind]
    return Path(settings.BASE_DIR) / "apps" / app / "providers" / f"{module_name_for(code)}.py"
